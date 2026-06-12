"""
GCSS-Army AUFK_WORKORDER → ALERP maintenance_orders Migration Script

Transforms maintenance work order data from the legacy GCSS-Army SAP system
into the unified ALERP maintenance_orders table format.

Field Mapping:
    AUFNR           → legacy_order_number (stripped leading zeros)
    AUART           → order_type (PM01=SCHEDULED, PM02=UNSCHEDULED, PM03=ANNUAL_SERVICE, PM04=MODIFICATION)
    KTEXT           → title (title-cased)
    KTEXT           → description (preserved as-is from source)
    EQUNR           → asset_id (UUID v5 generated from namespace + equipment number)
    PRIESSION       → priority (direct integer mapping: 1=URGENT, 2=HIGH, 3=ROUTINE)
    GSTRP           → scheduled_start
    GLTRP           → scheduled_end
    ERDAT           → created_at (with midnight UTC timestamp)
    ERNAM           → created_by (lowercased, @army.mil appended)
    ARBPL           → work_center
    IPHAS/OVERALL_STAT → status (combined mapping to ALERP status enum)
    KOSTL           → cost_center
    MAN_HOURS       → estimated_hours
    ACT_HOURS       → actual_hours
    FAULT_CODE      → fault_code
    TPLNR           → owning_uic (extracted from functional location path)

Idempotency:
    Uses UUID v5 with a fixed namespace so the same source record always
    produces the same order_id. Safe to re-run without duplicates.
"""

import uuid
import logging
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Fixed namespace UUID for deterministic ID generation (GCSS-Army work orders)
NAMESPACE_MAINTENANCE_ORDERS = uuid.UUID("d4e5f6a7-b8c9-0123-defa-234567890abc")

LEGACY_SYSTEM = "GCSS_ARMY"

# --- Mapping Tables ---

ORDER_TYPE_MAP: dict[str, str] = {
    "PM01": "SCHEDULED",
    "PM02": "UNSCHEDULED",
    "PM03": "ANNUAL_SERVICE",
    "PM04": "MODIFICATION",
}

# IPHAS (maintenance phase) + OVERALL_STAT (system status) → ALERP status
# Priority: IPHAS takes precedence where meaningful
PHASE_STATUS_MAP: dict[str, str] = {
    "PLAN": "PLANNED",
    "EXEC": "IN_PROGRESS",
    "WAIT": "AWAITING_PARTS",
    "COMP": "COMPLETED",
    "CANC": "CANCELLED",
}

SYSTEM_STATUS_MAP: dict[str, str] = {
    "CRTD": "CREATED",
    "REL": "IN_PROGRESS",
    "TECO": "COMPLETED",
    "CLSD": "COMPLETED",
    "DLFL": "CANCELLED",
}


# --- Transformation Helpers ---


def generate_order_id(aufnr: str) -> uuid.UUID:
    """Generate a deterministic UUID v5 from the source order number."""
    return uuid.uuid5(NAMESPACE_MAINTENANCE_ORDERS, aufnr.strip())


def generate_asset_id(equnr: str) -> uuid.UUID | None:
    """Generate a deterministic UUID v5 for asset FK from equipment number."""
    if not equnr or not equnr.strip():
        return None
    namespace_assets = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")
    return uuid.uuid5(namespace_assets, equnr.strip())


def map_order_type(auart: str | None) -> str:
    """Map SAP order category to ALERP order type enum."""
    if not auart:
        return "SCHEDULED"
    return ORDER_TYPE_MAP.get(auart.strip(), "SCHEDULED")


def map_priority(priession: str | None) -> int:
    """Map SAP priority to ALERP integer priority (1=URGENT, 2=HIGH, 3=ROUTINE)."""
    if not priession or not priession.strip():
        return 3  # Default to ROUTINE
    try:
        val = int(priession.strip())
        if val in (1, 2, 3):
            return val
        return 3
    except (ValueError, TypeError):
        return 3


def map_status(iphas: str | None, overall_stat: str | None) -> str:
    """Map SAP maintenance phase and system status to ALERP status enum."""
    phase = (iphas or "").strip().upper()
    stat = (overall_stat or "").strip().upper()

    # IPHAS takes precedence when available and meaningful
    if phase in PHASE_STATUS_MAP:
        return PHASE_STATUS_MAP[phase]
    if stat in SYSTEM_STATUS_MAP:
        return SYSTEM_STATUS_MAP[stat]
    return "CREATED"


def map_title(ktext: str | None) -> str:
    """Convert SAP short text to a readable title."""
    if not ktext or not ktext.strip():
        return "Untitled Maintenance Order"
    return ktext.strip().title()


def map_created_by(ernam: str | None) -> str:
    """Convert SAP username to email-style identifier."""
    if not ernam or not ernam.strip():
        return "system@army.mil"
    return f"{ernam.strip().lower()}@army.mil"


def parse_date(date_str: str | None) -> str | None:
    """Parse date string (YYYY-MM-DD or YYYYMMDD SAP format) and return ISO date."""
    if not date_str or not date_str.strip():
        return None
    clean = date_str.strip()
    # Handle SAP compact format YYYYMMDD
    if len(clean) == 8 and clean.isdigit():
        try:
            datetime.strptime(clean, "%Y%m%d")
            return f"{clean[:4]}-{clean[4:6]}-{clean[6:8]}"
        except ValueError:
            return None
    # Handle standard ISO format YYYY-MM-DD
    try:
        datetime.strptime(clean, "%Y-%m-%d")
        return clean
    except ValueError:
        return None


def parse_timestamp(date_str: str | None) -> str | None:
    """Parse date and return full ISO timestamp with UTC timezone."""
    parsed = parse_date(date_str)
    if not parsed:
        return None
    return f"{parsed}T00:00:00+00:00"


def parse_decimal(value: Any) -> Decimal | None:
    """Safely parse a decimal value."""
    if value is None:
        return None
    try:
        dec = Decimal(str(value))
        return dec
    except (InvalidOperation, ValueError, TypeError):
        return None


def extract_owning_uic(tplnr: str | None) -> str | None:
    """
    Extract a UIC-like identifier from the functional location path.
    TPLNR format: US-ARMY-III-1AD-2ABCT → derive unit code from hierarchy.
    Since TPLNR doesn't contain the actual UIC, we derive a placeholder
    from the last segment.
    """
    if not tplnr or not tplnr.strip():
        return None
    parts = tplnr.strip().split("-")
    # Return last meaningful segment as unit reference
    if len(parts) >= 4:
        return parts[-1][:6]
    return None


# --- Main Transformation ---


def transform_record(record: dict[str, Any]) -> dict[str, Any] | None:
    """
    Transform a single AUFK_WORKORDER record into a maintenance_orders record.

    Returns None if the record fails validation (missing required fields).
    """
    aufnr = record.get("AUFNR")
    if not aufnr or not str(aufnr).strip():
        logger.warning("Skipping record: missing AUFNR (order number)")
        return None

    aufnr_str = str(aufnr).strip()
    now_iso = datetime.now(timezone.utc).isoformat()

    asset_id = generate_asset_id(record.get("EQUNR", ""))

    transformed = {
        "order_id": str(generate_order_id(aufnr_str)),
        "legacy_system": LEGACY_SYSTEM,
        "legacy_order_number": aufnr_str.lstrip("0") or aufnr_str,
        "asset_id": str(asset_id) if asset_id else None,
        "order_type": map_order_type(record.get("AUART")),
        "title": map_title(record.get("KTEXT")),
        "description": (record.get("KTEXT") or "").strip() or None,
        "priority": map_priority(record.get("PRIESSION")),
        "status": map_status(record.get("IPHAS"), record.get("OVERALL_STAT")),
        "owning_uic": extract_owning_uic(record.get("TPLNR")),
        "work_center": (record.get("ARBPL") or "").strip() or None,
        "scheduled_start": parse_date(record.get("GSTRP")),
        "scheduled_end": parse_date(record.get("GLTRP")),
        "actual_start": None,  # Not available in source; populated post-migration
        "actual_end": None,
        "estimated_hours": parse_decimal(record.get("MAN_HOURS")),
        "actual_hours": parse_decimal(record.get("ACT_HOURS")),
        "fault_code": (record.get("FAULT_CODE") or "").strip() or None,
        "cost_center": (record.get("KOSTL") or "").strip() or None,
        "created_at": parse_timestamp(record.get("ERDAT")) or now_iso,
        "created_by": map_created_by(record.get("ERNAM")),
        "updated_at": now_iso,
    }

    return transformed


def validate_record(record: dict[str, Any]) -> list[str]:
    """Validate a transformed record. Returns a list of validation errors."""
    errors = []
    if not record.get("order_id"):
        errors.append("Missing order_id")
    if not record.get("legacy_order_number"):
        errors.append("Missing legacy_order_number")
    if record.get("order_type") not in ("SCHEDULED", "UNSCHEDULED", "ANNUAL_SERVICE", "MODIFICATION"):
        errors.append(f"Invalid order_type: {record.get('order_type')}")
    if record.get("priority") not in (1, 2, 3):
        errors.append(f"Invalid priority: {record.get('priority')}")
    if record.get("status") not in ("CREATED", "PLANNED", "IN_PROGRESS", "AWAITING_PARTS", "COMPLETED", "CANCELLED"):
        errors.append(f"Invalid status: {record.get('status')}")
    return errors


def run_migration(source_records: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Execute the full migration transformation.

    Args:
        source_records: List of AUFK_WORKORDER dicts from GCSS-Army.

    Returns:
        Dict with keys: 'records' (transformed), 'statistics' (counts/errors).
    """
    logger.info("=" * 60)
    logger.info("GCSS-Army AUFK_WORKORDER → ALERP maintenance_orders")
    logger.info("=" * 60)
    logger.info("Source records: %d", len(source_records))

    transformed_records: list[dict[str, Any]] = []
    skipped = 0
    validation_errors: list[dict[str, Any]] = []

    for i, record in enumerate(source_records):
        result = transform_record(record)
        if result is None:
            skipped += 1
            continue

        errors = validate_record(result)
        if errors:
            validation_errors.append({
                "record_index": i,
                "aufnr": record.get("AUFNR"),
                "errors": errors,
            })
            logger.warning(
                "Validation errors for record %d (AUFNR=%s): %s",
                i, record.get("AUFNR"), errors,
            )
            # Still include record; errors are non-fatal warnings
        transformed_records.append(result)

    statistics = {
        "total_source_records": len(source_records),
        "successfully_transformed": len(transformed_records),
        "skipped": skipped,
        "validation_warnings": len(validation_errors),
        "validation_details": validation_errors,
    }

    logger.info("-" * 60)
    logger.info("Migration complete.")
    logger.info("  Transformed: %d", statistics["successfully_transformed"])
    logger.info("  Skipped:     %d", statistics["skipped"])
    logger.info("  Warnings:    %d", statistics["validation_warnings"])
    logger.info("=" * 60)

    return {"records": transformed_records, "statistics": statistics}


# --- Sample Data & Entrypoint ---

SAMPLE_SOURCE_DATA = [
    {
        "AUFNR": "000004521001",
        "AUTYP": "PM",
        "AUART": "PM01",
        "KTEXT": "SCHEDULED MAINT - ENGINE OVERHAUL",
        "EQUNR": "000000000010045231",
        "TPLNR": "US-ARMY-III-1AD-2ABCT",
        "PRIESSION": "2",
        "GSTRP": "2024-02-01",
        "GLTRP": "2024-02-15",
        "ERDAT": "2024-01-20",
        "ERNAM": "CW3.MARTINEZ",
        "ARBPL": "MAINT_3A",
        "IPHAS": "EXEC",
        "KOSTL": "CC-1AD-MNT",
        "OVERALL_STAT": "REL",
        "MAN_HOURS": 240.0,
        "ACT_HOURS": 186.5,
        "FAULT_CODE": "ENG-0042",
    },
    {
        "AUFNR": "000004521002",
        "AUTYP": "PM",
        "AUART": "PM02",
        "KTEXT": "UNSCHEDULED - TRANSMISSION FAULT",
        "EQUNR": "000000000010045250",
        "TPLNR": "US-ARMY-III-1AD-2ABCT",
        "PRIESSION": "1",
        "GSTRP": "2024-01-16",
        "GLTRP": "2024-01-25",
        "ERDAT": "2024-01-15",
        "ERNAM": "SFC.THOMPSON",
        "ARBPL": "MAINT_2B",
        "IPHAS": "WAIT",
        "KOSTL": "CC-1AD-MNT",
        "OVERALL_STAT": "REL",
        "MAN_HOURS": 80.0,
        "ACT_HOURS": 0.0,
        "FAULT_CODE": "TRN-0018",
    },
    {
        "AUFNR": "000004521003",
        "AUTYP": "PM",
        "AUART": "PM03",
        "KTEXT": "ANNUAL SERVICE - TURRET SYSTEMS",
        "EQUNR": "000000000010045232",
        "TPLNR": "US-ARMY-III-1AD-2ABCT",
        "PRIESSION": "3",
        "GSTRP": "2024-03-01",
        "GLTRP": "2024-03-05",
        "ERDAT": "2024-01-22",
        "ERNAM": "CW3.MARTINEZ",
        "ARBPL": "MAINT_3A",
        "IPHAS": "PLAN",
        "KOSTL": "CC-1AD-MNT",
        "OVERALL_STAT": "CRTD",
        "MAN_HOURS": 40.0,
        "ACT_HOURS": 0.0,
        "FAULT_CODE": "",
    },
]


if __name__ == "__main__":
    result = run_migration(SAMPLE_SOURCE_DATA)
    print(f"\nTransformed {result['statistics']['successfully_transformed']} records:")
    for rec in result["records"]:
        print(f"  {rec['order_id']} | {rec['legacy_order_number']} | "
              f"{rec['order_type']} | {rec['status']} | {rec['title']}")
