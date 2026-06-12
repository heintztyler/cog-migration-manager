"""
LMP SHIPMENT_TRACKING → ALERP shipments Migration Script

Transforms shipment/transportation records from the legacy LMP system's
SHIPMENT_TRACKING table into the unified ALERP shipments table format.

Field Mapping:
    SHIPMENT_ID      → legacy_shipment_id (preserved as-is)
    (generated)      → shipment_id (new UUID)
    (constant "LMP") → legacy_system
    SHIP_TYPE        → shipment_type (validated against enum)
    TCN              → tcn
    ORIGIN_DODAAC    → origin_dodaac
    ORIGIN_NAME      → origin_name
    DEST_DODAAC      → destination_dodaac
    DEST_NAME        → destination_name
    MATERIAL_NUM/NSN → item_id (placeholder UUID via deterministic seed)
    PO_REFERENCE     → procurement_order_id (placeholder UUID via deterministic seed)
    QUANTITY         → quantity
    WEIGHT_LBS       → weight_lbs
    SHIP_DATE        → ship_date
    ETA_DATE         → estimated_arrival
    ACTUAL_ARRIVAL   → actual_arrival (NULL preserved for in-transit)
    CARRIER          → carrier
    TRACKING_STATUS  → status (mapped to target enum)
    HAZMAT_CLASS     → hazmat_class
    (generated)      → created_at, updated_at (audit timestamps)

Status Mapping:
    IN_TRANSIT → IN_TRANSIT
    DELIVERED  → DELIVERED
    PENDING    → PENDING
    RETURNED   → RETURNED
    CANCELLED  → RETURNED  (closest match)
    SHIPPED    → IN_TRANSIT (alias)

Idempotency:
    Uses uuid5 with a fixed namespace so the same source record always
    produces the same shipment_id. Re-running the script on identical
    input yields identical output.
"""

import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Optional

logger = logging.getLogger(__name__)

LEGACY_SYSTEM = "LMP"

# Fixed namespace for deterministic UUID generation (idempotency)
_NAMESPACE_SHIPMENTS = uuid.UUID("d1a7e3f0-5b2c-4e8a-9f01-2345abcdef67")
_NAMESPACE_ITEMS = uuid.UUID("a2b3c4d5-e6f7-4890-ab12-cdef34567890")
_NAMESPACE_PO = uuid.UUID("b3c4d5e6-f7a8-4901-bc23-def456789012")

VALID_SHIPMENT_TYPES = {"SURFACE", "AIR", "SEALIFT", "MULTIMODAL"}

STATUS_MAP = {
    "IN_TRANSIT": "IN_TRANSIT",
    "DELIVERED": "DELIVERED",
    "PENDING": "PENDING",
    "RETURNED": "RETURNED",
    "CANCELLED": "RETURNED",
    "SHIPPED": "IN_TRANSIT",
}


class ValidationError(Exception):
    """Raised when a source record fails validation."""


class MigrationStats:
    """Tracks transformation statistics."""

    def __init__(self):
        self.total = 0
        self.transformed = 0
        self.skipped = 0
        self.errors = 0
        self.error_details: list[dict] = []

    def record_error(self, record_id: str, error: str):
        self.errors += 1
        self.error_details.append({"record_id": record_id, "error": error})

    def summary(self) -> dict:
        return {
            "total_records": self.total,
            "transformed": self.transformed,
            "skipped": self.skipped,
            "errors": self.errors,
            "error_details": self.error_details,
        }


def generate_shipment_id(legacy_id: str) -> str:
    """Generate a deterministic UUID for a shipment based on its legacy ID."""
    return str(uuid.uuid5(_NAMESPACE_SHIPMENTS, f"{LEGACY_SYSTEM}:{legacy_id}"))


def generate_item_id(material_num: str, nsn: str) -> Optional[str]:
    """Generate a deterministic placeholder UUID for item_id from material/NSN.

    In a full migration the item_id would be looked up from the already-migrated
    supply_items table. Here we generate a stable placeholder so the FK can be
    resolved in a subsequent reconciliation pass.
    """
    key = material_num or nsn
    if not key or not key.strip():
        return None
    return str(uuid.uuid5(_NAMESPACE_ITEMS, key.strip()))


def generate_procurement_order_id(po_reference: str) -> Optional[str]:
    """Generate a deterministic placeholder UUID for procurement_order_id.

    Same rationale as generate_item_id — real FK resolution happens after
    the procurement_orders migration has run.
    """
    if not po_reference or not po_reference.strip():
        return None
    return str(uuid.uuid5(_NAMESPACE_PO, po_reference.strip()))


def parse_date(value) -> Optional[str]:
    """Normalise a date value to ISO-8601 string (YYYY-MM-DD).

    Accepts strings in YYYY-MM-DD or YYYYMMDD (SAP internal) format,
    datetime objects, or None.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    if hasattr(value, "isoformat"):
        return value.isoformat()
    raw = str(value).strip()
    if not raw:
        return None
    # YYYY-MM-DD
    if len(raw) == 10 and raw[4] == "-" and raw[7] == "-":
        datetime.strptime(raw, "%Y-%m-%d")
        return raw
    # YYYYMMDD (SAP internal format)
    if len(raw) == 8 and raw.isdigit():
        dt = datetime.strptime(raw, "%Y%m%d")
        return dt.strftime("%Y-%m-%d")
    raise ValueError(f"Unrecognised date format: {raw!r}")


def parse_decimal(value, field_name: str) -> Optional[Decimal]:
    """Parse a numeric value into a Decimal, returning None for empty/null."""
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    raw = str(value).strip()
    if not raw:
        return None
    try:
        return Decimal(raw)
    except InvalidOperation:
        raise ValueError(f"Invalid decimal value for {field_name}: {raw!r}")


def map_shipment_type(ship_type: str) -> str:
    """Validate and map SHIP_TYPE to the target shipment_type enum."""
    if not ship_type or not ship_type.strip():
        return "SURFACE"  # default
    normalised = ship_type.strip().upper()
    if normalised in VALID_SHIPMENT_TYPES:
        return normalised
    logger.warning("Unknown SHIP_TYPE %r, defaulting to SURFACE", ship_type)
    return "SURFACE"


def map_status(tracking_status: str) -> str:
    """Map TRACKING_STATUS to the target status enum."""
    if not tracking_status or not tracking_status.strip():
        return "PENDING"
    normalised = tracking_status.strip().upper()
    mapped = STATUS_MAP.get(normalised)
    if mapped:
        return mapped
    logger.warning("Unknown TRACKING_STATUS %r, defaulting to PENDING", tracking_status)
    return "PENDING"


def validate_record(record: dict) -> list[str]:
    """Return a list of validation warnings/errors for a source record."""
    issues: list[str] = []
    if not record.get("SHIPMENT_ID"):
        issues.append("Missing required field SHIPMENT_ID")
    if not record.get("ORIGIN_DODAAC"):
        issues.append("Missing ORIGIN_DODAAC")
    if not record.get("DEST_DODAAC"):
        issues.append("Missing DEST_DODAAC")
    dodaac_fields = ["ORIGIN_DODAAC", "DEST_DODAAC"]
    for field in dodaac_fields:
        val = record.get(field)
        if val and len(str(val).strip()) > 6:
            issues.append(f"{field} exceeds 6 characters: {val!r}")
    return issues


def transform_record(record: dict, now: Optional[str] = None) -> dict:
    """Transform a single LMP SHIPMENT_TRACKING record to ALERP shipments format.

    Args:
        record: Source record as a dict with LMP field names.
        now: ISO-8601 timestamp for audit fields. Defaults to current UTC time.

    Returns:
        Transformed record dict with ALERP field names.

    Raises:
        ValidationError: If the record is missing critical fields.
    """
    issues = validate_record(record)
    critical = [i for i in issues if "Missing required" in i]
    if critical:
        raise ValidationError("; ".join(critical))

    if now is None:
        now = datetime.now(timezone.utc).isoformat()

    legacy_id = str(record["SHIPMENT_ID"]).strip()

    return {
        "shipment_id": generate_shipment_id(legacy_id),
        "legacy_system": LEGACY_SYSTEM,
        "legacy_shipment_id": legacy_id,
        "tcn": (record.get("TCN") or "").strip() or None,
        "shipment_type": map_shipment_type(record.get("SHIP_TYPE", "")),
        "origin_dodaac": (record.get("ORIGIN_DODAAC") or "").strip() or None,
        "origin_name": (record.get("ORIGIN_NAME") or "").strip() or None,
        "destination_dodaac": (record.get("DEST_DODAAC") or "").strip() or None,
        "destination_name": (record.get("DEST_NAME") or "").strip() or None,
        "item_id": generate_item_id(
            record.get("MATERIAL_NUM", ""),
            record.get("NSN", ""),
        ),
        "procurement_order_id": generate_procurement_order_id(
            record.get("PO_REFERENCE", ""),
        ),
        "quantity": parse_decimal(record.get("QUANTITY"), "QUANTITY"),
        "weight_lbs": parse_decimal(record.get("WEIGHT_LBS"), "WEIGHT_LBS"),
        "ship_date": parse_date(record.get("SHIP_DATE")),
        "estimated_arrival": parse_date(record.get("ETA_DATE")),
        "actual_arrival": parse_date(record.get("ACTUAL_ARRIVAL")),
        "carrier": (record.get("CARRIER") or "").strip() or None,
        "status": map_status(record.get("TRACKING_STATUS", "")),
        "hazmat_class": (record.get("HAZMAT_CLASS") or "").strip() or None,
        "created_at": now,
        "updated_at": now,
    }


def run_migration(
    source_records: list[dict],
    now: Optional[str] = None,
) -> tuple[list[dict], MigrationStats]:
    """Transform a batch of LMP SHIPMENT_TRACKING records.

    Args:
        source_records: List of source record dicts.
        now: Fixed timestamp for audit fields (useful for testing).

    Returns:
        Tuple of (transformed_records, stats).
    """
    stats = MigrationStats()
    stats.total = len(source_records)
    transformed: list[dict] = []

    for idx, record in enumerate(source_records):
        record_id = record.get("SHIPMENT_ID", f"<index {idx}>")
        try:
            result = transform_record(record, now=now)
            transformed.append(result)
            stats.transformed += 1
        except ValidationError as exc:
            logger.warning("Skipping record %s: %s", record_id, exc)
            stats.skipped += 1
            stats.record_error(str(record_id), f"Validation: {exc}")
        except Exception as exc:
            logger.error("Error transforming record %s: %s", record_id, exc)
            stats.record_error(str(record_id), str(exc))

    logger.info(
        "Migration complete: %d total, %d transformed, %d skipped, %d errors",
        stats.total,
        stats.transformed,
        stats.skipped,
        stats.errors,
    )
    return transformed, stats


# ---------------------------------------------------------------------------
# CLI entry point — run against the built-in sample data for quick validation
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import json
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # Import sample data from the repo's schema definitions
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))
    try:
        from backend.app.legacy_systems.system_bravo import SAMPLE_DATA

        source = SAMPLE_DATA["SHIPMENT_TRACKING"]
    except ImportError:
        logger.info("Could not import sample data; using inline sample records")
        source = [
            {
                "SHIPMENT_ID": "SHP-00891234",
                "SHIP_TYPE": "SURFACE",
                "TCN": "W45G09-4108-0001",
                "ORIGIN_DODAAC": "W45G09",
                "ORIGIN_NAME": "ANNISTON ARMY DEPOT",
                "DEST_DODAAC": "W45XAA",
                "DEST_NAME": "2ABCT, 1AD - FORT BLISS",
                "MATERIAL_NUM": "000000000050012345",
                "NSN": "2940-01-576-4108",
                "QUANTITY": 100.0,
                "WEIGHT_LBS": 245.0,
                "SHIP_DATE": "2024-01-10",
                "ETA_DATE": "2024-01-17",
                "ACTUAL_ARRIVAL": None,
                "CARRIER": "DLA DISTRIBUTION",
                "TRACKING_STATUS": "IN_TRANSIT",
                "PO_REFERENCE": "4500089231",
                "HAZMAT_CLASS": "NONE",
            },
            {
                "SHIPMENT_ID": "SHP-00891200",
                "SHIP_TYPE": "SURFACE",
                "TCN": "W45G09-4455-0001",
                "ORIGIN_DODAAC": "W45G09",
                "ORIGIN_NAME": "ANNISTON ARMY DEPOT",
                "DEST_DODAAC": "W45XBB",
                "DEST_NAME": "DIVARTY, 1AD - FORT BLISS",
                "MATERIAL_NUM": "000000000050012400",
                "NSN": "2530-01-595-4455",
                "QUANTITY": 50.0,
                "WEIGHT_LBS": 3600.0,
                "SHIP_DATE": "2024-01-08",
                "ETA_DATE": "2024-01-15",
                "ACTUAL_ARRIVAL": "2024-01-14",
                "CARRIER": "DLA DISTRIBUTION",
                "TRACKING_STATUS": "DELIVERED",
                "PO_REFERENCE": "4500089250",
                "HAZMAT_CLASS": "NONE",
            },
        ]

    results, migration_stats = run_migration(source)

    print("\n=== Migration Results ===")
    print(json.dumps(migration_stats.summary(), indent=2))
    print(f"\nTransformed {len(results)} record(s):\n")
    for rec in results:
        serialisable = {
            k: str(v) if isinstance(v, Decimal) else v for k, v in rec.items()
        }
        print(json.dumps(serialisable, indent=2))
