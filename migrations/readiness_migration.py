"""
GCSS-Army UNIT_READINESS -> ALERP readiness_reports Migration Script

Transforms data from the legacy GCSS-Army UNIT_READINESS table into the
unified ALERP readiness_reports table format.

Field Mapping:
    Source (UNIT_READINESS)         Target (readiness_reports)
    -------------------------      ---------------------------
    (generated)                    report_id           UUID
    (constant: "GCSS_ARMY")        legacy_system       VARCHAR(20)
    REPORT_ID                      legacy_report_id    VARCHAR(30)
    UIC                            uic                 VARCHAR(6)
    UNIT_NAME                      unit_name           VARCHAR(80)
    REPORT_DATE                    report_date         DATE (ISO 8601)
    EQUIP_CAT                      asset_category      VARCHAR(30)
    AUTH_QTY                       authorized_quantity INTEGER
    ON_HAND                        on_hand_quantity    INTEGER
    FMC_QTY                        fmc_quantity        INTEGER
    PMC_QTY                        pmc_quantity        INTEGER
    NMC_QTY                        nmc_quantity        INTEGER
    FMC_RATE                       fmc_rate            DECIMAL(5,2)
    DEADLINE_QTY                   deadline_quantity   INTEGER
    REMARKS                        commander_remarks   TEXT
    (generated)                    created_at          TIMESTAMP WITH TIME ZONE

Notes:
    - EQUIP_CAT values are mapped to standardised asset_category enums via
      EQUIP_CAT_MAP (e.g. "TRACKED_VH" -> "TRACKED_VEHICLE").
    - FMC_RATE is recomputed from FMC_QTY / ON_HAND when ON_HAND > 0,
      falling back to the source value if ON_HAND is zero or missing.
    - The script is idempotent: running it twice on the same input produces
      deterministic UUIDs (uuid5 seeded on REPORT_ID + EQUIP_CAT), so
      duplicate inserts can be detected downstream.
"""

import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

LEGACY_SYSTEM = "GCSS_ARMY"

# Deterministic UUID namespace for idempotent key generation
_UUID_NAMESPACE = uuid.UUID("c9a1e2b3-d4f5-6789-abcd-ef0123456789")

# Equipment category normalisation map
EQUIP_CAT_MAP: dict[str, str] = {
    "TRACKED_VH": "TRACKED_VEHICLE",
    "WHEELED_VH": "WHEELED_VEHICLE",
    "TOWED_ART": "TOWED_ARTILLERY",
    "SP_ART": "SELF_PROPELLED_ARTILLERY",
    "SMALL_ARMS": "SMALL_ARMS",
    "COMMS": "COMMUNICATIONS",
    "C4ISR": "C4ISR",
    "AIRCRAFT": "AIRCRAFT",
    "WATERCRAFT": "WATERCRAFT",
    "ENGR_EQUIP": "ENGINEER_EQUIPMENT",
    "NBC_EQUIP": "CBRN_EQUIPMENT",
    "MISSILE": "MISSILE_SYSTEM",
    "UAV": "UNMANNED_AERIAL_SYSTEM",
    "GEN_PWR": "GENERATOR_POWER",
}

REQUIRED_SOURCE_FIELDS = (
    "REPORT_ID",
    "UIC",
    "REPORT_DATE",
    "EQUIP_CAT",
)


def _generate_report_uuid(report_id: str, equip_cat: str) -> str:
    """Deterministic UUID from REPORT_ID + EQUIP_CAT for idempotency."""
    seed = f"{report_id}|{equip_cat}"
    return str(uuid.uuid5(_UUID_NAMESPACE, seed))


def _normalise_equip_cat(value: str | None) -> str:
    """Map legacy equipment category to standardised enum."""
    if not value:
        return "UNKNOWN"
    normalised = value.strip().upper()
    return EQUIP_CAT_MAP.get(normalised, normalised)


def _parse_date(value) -> str | None:
    """Accept ISO-8601 date strings and common SAP date formats."""
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%Y%m%d", "%d.%m.%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    logger.warning("Unparseable date value: %s", raw)
    return raw


def _safe_int(value, default: int = 0) -> int:
    """Convert a value to int, returning *default* on failure."""
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _safe_decimal(value, default: str = "0.00") -> str:
    """Convert a value to a DECIMAL(5,2) string representation."""
    if value is None:
        return default
    try:
        d = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return str(d)
    except (InvalidOperation, ValueError, TypeError):
        return default


def _safe_str(value) -> str | None:
    """Convert a value to a stripped string, returning None for empty/None."""
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None


def _compute_fmc_rate(fmc_qty: int, on_hand: int, source_rate) -> str:
    """Recompute FMC rate from quantities; fall back to source value."""
    if on_hand > 0:
        rate = Decimal(fmc_qty * 100) / Decimal(on_hand)
        return str(rate.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    return _safe_decimal(source_rate)


def _validate_record(record: dict, index: int) -> list[str]:
    """Return a list of validation error strings (empty = valid)."""
    errors: list[str] = []
    for field in REQUIRED_SOURCE_FIELDS:
        val = record.get(field)
        if val is None or (isinstance(val, str) and not val.strip()):
            errors.append(f"Record {index}: missing required field '{field}'")

    auth = _safe_int(record.get("AUTH_QTY"), -1)
    on_hand = _safe_int(record.get("ON_HAND"), -1)
    fmc = _safe_int(record.get("FMC_QTY"), -1)
    if auth < 0 or on_hand < 0 or fmc < 0:
        errors.append(f"Record {index}: quantity fields must be non-negative integers")

    return errors


def transform_record(record: dict) -> dict:
    """Transform a single UNIT_READINESS row into a readiness_reports row."""
    report_id = str(record.get("REPORT_ID", "")).strip()
    equip_cat = str(record.get("EQUIP_CAT", "")).strip()

    on_hand = _safe_int(record.get("ON_HAND"))
    fmc_qty = _safe_int(record.get("FMC_QTY"))

    return {
        "report_id": _generate_report_uuid(report_id, equip_cat),
        "legacy_system": LEGACY_SYSTEM,
        "legacy_report_id": report_id,
        "uic": _safe_str(record.get("UIC")),
        "unit_name": _safe_str(record.get("UNIT_NAME")),
        "report_date": _parse_date(record.get("REPORT_DATE")),
        "asset_category": _normalise_equip_cat(equip_cat),
        "authorized_quantity": _safe_int(record.get("AUTH_QTY")),
        "on_hand_quantity": on_hand,
        "fmc_quantity": fmc_qty,
        "pmc_quantity": _safe_int(record.get("PMC_QTY")),
        "nmc_quantity": _safe_int(record.get("NMC_QTY")),
        "fmc_rate": _compute_fmc_rate(fmc_qty, on_hand, record.get("FMC_RATE")),
        "deadline_quantity": _safe_int(record.get("DEADLINE_QTY")),
        "commander_remarks": _safe_str(record.get("REMARKS")),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def migrate(source_records: list[dict]) -> dict:
    """
    Run the full migration pipeline.

    Returns a summary dict:
        {
            "transformed": [<list of target dicts>],
            "total":       int,
            "succeeded":   int,
            "skipped":     int,
            "errors":      [<list of error message strings>],
        }
    """
    total = len(source_records)
    transformed: list[dict] = []
    all_errors: list[str] = []
    skipped = 0

    logger.info("Starting readiness migration: %d source records", total)

    for idx, record in enumerate(source_records):
        validation_errors = _validate_record(record, idx)
        if validation_errors:
            all_errors.extend(validation_errors)
            skipped += 1
            logger.warning("Skipping record %d: %s", idx, "; ".join(validation_errors))
            continue

        try:
            transformed.append(transform_record(record))
        except Exception as exc:
            msg = f"Record {idx}: transformation error - {exc}"
            all_errors.append(msg)
            skipped += 1
            logger.error(msg)

    succeeded = len(transformed)
    logger.info(
        "Migration complete: %d total, %d succeeded, %d skipped, %d errors",
        total, succeeded, skipped, len(all_errors),
    )

    return {
        "transformed": transformed,
        "total": total,
        "succeeded": succeeded,
        "skipped": skipped,
        "errors": all_errors,
    }


# ---------------------------------------------------------------------------
# CLI entry point with sample data
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    sample_data = [
        {
            "REPORT_ID": "USR-2024-0115-1AD",
            "UIC": "W45XAA",
            "UNIT_NAME": "2D ABCT, 1ST ARMORED DIV",
            "REPORT_DATE": "2024-01-15",
            "EQUIP_CAT": "TRACKED_VH",
            "AUTH_QTY": 58,
            "ON_HAND": 56,
            "FMC_QTY": 48,
            "PMC_QTY": 5,
            "NMC_QTY": 3,
            "FMC_RATE": 85.71,
            "DEADLINE_QTY": 2,
            "REMARKS": "2x M1A2 AWAITING POWERPACK; ESD 30JAN",
        },
        {
            "REPORT_ID": "USR-2024-0115-1AD",
            "UIC": "W45XAA",
            "UNIT_NAME": "2D ABCT, 1ST ARMORED DIV",
            "REPORT_DATE": "2024-01-15",
            "EQUIP_CAT": "WHEELED_VH",
            "AUTH_QTY": 245,
            "ON_HAND": 240,
            "FMC_QTY": 218,
            "PMC_QTY": 12,
            "NMC_QTY": 10,
            "FMC_RATE": 90.83,
            "DEADLINE_QTY": 4,
            "REMARKS": "4x HMMWV AT DEPOT; 3x NMC TRANS FAULT",
        },
        {
            "REPORT_ID": "USR-2024-0115-DIV",
            "UIC": "W45XBB",
            "UNIT_NAME": "DIVARTY, 1ST ARMORED DIV",
            "REPORT_DATE": "2024-01-15",
            "EQUIP_CAT": "TRACKED_VH",
            "AUTH_QTY": 24,
            "ON_HAND": 24,
            "FMC_QTY": 22,
            "PMC_QTY": 1,
            "NMC_QTY": 1,
            "FMC_RATE": 91.67,
            "DEADLINE_QTY": 0,
            "REMARKS": "1x M109A7 NMC FIRE CONTROL; PARTS ON ORDER",
        },
    ]

    result = migrate(sample_data)

    print(f"\nTotal: {result['total']}")
    print(f"Succeeded: {result['succeeded']}")
    print(f"Skipped: {result['skipped']}")

    print("\nTransformed records:")
    for rec in result["transformed"]:
        for k, v in rec.items():
            print(f"  {k}: {v}")
        print()

    if result["errors"]:
        print("Errors:")
        for err in result["errors"]:
            print(f"  {err}")
