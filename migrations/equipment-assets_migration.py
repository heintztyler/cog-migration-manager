"""
Equipment-Assets Migration Script
==================================
Transforms GCSS-Army EQUI_MASTER records into ALERP unified `assets` table format.

Mapping Logic
-------------
Direct mappings:
    EQUNR       -> legacy_id          (strip leading zeros for readability? No — preserve verbatim)
    NSN         -> nsn
    LIN_NUM     -> lin
    TXTMI       -> nomenclature AND short_name (nomenclature = full text; short_name = first 50 chars)
    SERGE       -> serial_number
    HERST       -> manufacturer
    ANSDT       -> acquisition_date
    ANSWT       -> acquisition_cost   (converted to Decimal with 2-place precision)
    INBDT       -> fielding_date      (start-up date = date fielded to unit)
    UIC         -> owning_uic
    IWERK       -> installation       (maintenance plant code used as installation proxy)
    STORT       -> location_detail    (storage location)
    USTATUS     -> readiness_status   (FMC/PMC/NMC passed through)
    STATTEXT    -> status_reason      (blank when FMC; carried over otherwise)
    AENAM       -> updated_by

Derived / constant fields:
    asset_id        -> generated UUID (deterministic from legacy_system + legacy_id for idempotency)
    legacy_system   -> "GCSS_ARMY"
    asset_category  -> mapped from EQTYP + EQART via CATEGORY_MAP
    manufacturer_cage -> None (not available in source)
    owning_unit_name  -> derived from TPLNR functional location path
    created_at / updated_at -> current UTC timestamp at migration time

Currency handling:
    Only USD values are migrated; non-USD rows are flagged and skipped.
"""

import logging
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

LEGACY_SYSTEM = "GCSS_ARMY"

# Deterministic UUID namespace for idempotent key generation
_NAMESPACE_ALERP = uuid.UUID("f47ac10b-58cc-4372-a567-0d02b2c3d479")

# Equipment category mapping: (EQTYP, EQART) -> asset_category
CATEGORY_MAP: dict[tuple[str, str], str] = {
    ("V", "TRACKED_VH"): "TRACKED_VEHICLE",
    ("V", "WHEELED_VH"): "WHEELED_VEHICLE",
    ("V", "AIRCRAFT"): "ROTARY_WING",
    ("V", "FIXED_WNG"): "FIXED_WING",
    ("W", "SMALL_ARM"): "SMALL_ARMS",
    ("W", "CREW_SRVD"): "CREW_SERVED_WEAPON",
    ("W", "MISSILE"): "MISSILE_SYSTEM",
    ("C", "C4ISR"): "C4ISR",
    ("C", "COMMS"): "COMMUNICATIONS",
    ("E", "GEN_EQUIP"): "GENERAL_EQUIPMENT",
}
EQTYP_FALLBACK: dict[str, str] = {
    "V": "VEHICLE",
    "W": "WEAPON_SYSTEM",
    "C": "C4ISR",
    "E": "GENERAL_EQUIPMENT",
}

VALID_READINESS = {"FMC", "PMC", "NMC"}


def _generate_asset_id(legacy_id: str) -> str:
    """Deterministic UUID from legacy system + id so re-runs produce the same key."""
    return str(uuid.uuid5(_NAMESPACE_ALERP, f"{LEGACY_SYSTEM}:{legacy_id}"))


def _parse_date(value: Optional[str]) -> Optional[str]:
    """Parse a date string and return ISO-8601 date or None."""
    if not value or str(value).strip() == "":
        return None
    raw = str(value).strip()
    # SAP sometimes uses YYYYMMDD format
    if len(raw) == 8 and raw.isdigit():
        try:
            d = datetime.strptime(raw, "%Y%m%d").date()
            return d.isoformat()
        except ValueError:
            return None
    # Standard ISO date
    try:
        d = date.fromisoformat(raw)
        return d.isoformat()
    except (ValueError, TypeError):
        return None


def _parse_decimal(value) -> Optional[str]:
    """Convert a numeric value to a Decimal string with 2-place precision."""
    if value is None:
        return None
    try:
        d = Decimal(str(value)).quantize(Decimal("0.01"))
        return str(d)
    except (InvalidOperation, TypeError, ValueError):
        return None


def _resolve_category(eqtyp: Optional[str], eqart: Optional[str]) -> str:
    """Map EQTYP + EQART to a unified asset_category."""
    eqtyp = (eqtyp or "").strip().upper()
    eqart = (eqart or "").strip().upper()
    category = CATEGORY_MAP.get((eqtyp, eqart))
    if category:
        return category
    return EQTYP_FALLBACK.get(eqtyp, "UNKNOWN")


def _extract_unit_name(tplnr: Optional[str]) -> Optional[str]:
    """
    Derive a human-readable owning unit name from the TPLNR functional location.
    Example: 'US-ARMY-III-1AD-2ABCT' -> '2ABCT, 1AD'
    """
    if not tplnr or str(tplnr).strip() == "":
        return None
    parts = str(tplnr).strip().split("-")
    if len(parts) >= 5:
        return f"{parts[-1]}, {parts[-2]}"
    if len(parts) >= 2:
        return parts[-1]
    return tplnr


def _safe_str(value, max_len: Optional[int] = None) -> Optional[str]:
    """Return stripped string or None for empty/null values."""
    if value is None:
        return None
    s = str(value).strip()
    if s == "":
        return None
    if max_len:
        s = s[:max_len]
    return s


def _normalize_readiness(status: Optional[str]) -> Optional[str]:
    """Validate and normalise readiness status to FMC/PMC/NMC."""
    if not status:
        return None
    s = str(status).strip().upper()
    return s if s in VALID_READINESS else None


def transform_record(record: dict) -> dict:
    """
    Transform a single EQUI_MASTER record into an ALERP assets row.

    Returns a dict matching the target schema.  Raises ValueError for
    records that cannot be migrated (e.g. missing EQUNR).
    """
    equnr = _safe_str(record.get("EQUNR"))
    if not equnr:
        raise ValueError("Record missing required field EQUNR")

    now = datetime.now(timezone.utc).isoformat()

    readiness = _normalize_readiness(record.get("USTATUS"))
    status_text = _safe_str(record.get("STATTEXT"), 100)
    # Only carry status_reason when the asset is not fully mission capable
    status_reason = status_text if readiness and readiness != "FMC" else None

    nomenclature = _safe_str(record.get("TXTMI"), 100)

    return {
        "asset_id": _generate_asset_id(equnr),
        "legacy_system": LEGACY_SYSTEM,
        "legacy_id": equnr,
        "nsn": _safe_str(record.get("NSN")),
        "lin": _safe_str(record.get("LIN_NUM"), 10),
        "nomenclature": nomenclature,
        "short_name": nomenclature[:50] if nomenclature else None,
        "asset_category": _resolve_category(
            record.get("EQTYP"), record.get("EQART")
        ),
        "serial_number": _safe_str(record.get("SERGE"), 30),
        "manufacturer": _safe_str(record.get("HERST"), 80),
        "manufacturer_cage": None,  # not available in GCSS-Army source
        "acquisition_date": _parse_date(record.get("ANSDT")),
        "acquisition_cost": _parse_decimal(record.get("ANSWT")),
        "fielding_date": _parse_date(record.get("INBDT")),
        "owning_uic": _safe_str(record.get("UIC"), 6),
        "owning_unit_name": _extract_unit_name(record.get("TPLNR")),
        "installation": _safe_str(record.get("IWERK"), 50),
        "location_detail": _safe_str(record.get("STORT"), 50),
        "readiness_status": readiness,
        "status_reason": status_reason,
        "created_at": now,
        "updated_at": now,
        "updated_by": _safe_str(record.get("AENAM"), 50),
    }


def migrate(source_records: list[dict]) -> dict:
    """
    Run the full migration over a list of EQUI_MASTER dicts.

    Returns a summary dict:
        transformed  - list of successfully transformed asset rows
        errors       - list of (index, error_message) for failed records
        stats        - counts for processed / succeeded / skipped / errored
    """
    transformed: list[dict] = []
    errors: list[tuple[int, str]] = []
    skipped = 0

    for idx, record in enumerate(source_records):
        # Skip non-USD records
        currency = _safe_str(record.get("WAESSION"))
        if currency and currency.upper() != "USD":
            logger.warning(
                "Record %d (EQUNR=%s): non-USD currency '%s' — skipped",
                idx, record.get("EQUNR"), currency,
            )
            skipped += 1
            continue

        try:
            row = transform_record(record)
            transformed.append(row)
        except (ValueError, KeyError, TypeError) as exc:
            logger.error("Record %d (EQUNR=%s): %s", idx, record.get("EQUNR"), exc)
            errors.append((idx, str(exc)))

    stats = {
        "total_input": len(source_records),
        "succeeded": len(transformed),
        "skipped": skipped,
        "errors": len(errors),
    }

    logger.info(
        "Migration complete — %d input, %d succeeded, %d skipped, %d errors",
        stats["total_input"], stats["succeeded"], stats["skipped"], stats["errors"],
    )
    return {"transformed": transformed, "errors": errors, "stats": stats}


# ---------------------------------------------------------------------------
# CLI entry point — run standalone for ad-hoc testing
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    SAMPLE_DATA = [
        {
            "EQUNR": "000000000010045231", "EQTYP": "V",
            "TXTMI": "M1A2 ABRAMS MAIN BATTLE TANK", "EQART": "TRACKED_VH",
            "INBDT": "2019-03-15", "HERST": "GENERAL DYNAMICS LAND SYSTEMS",
            "SERGE": "GDLS-2019-4521", "ANSDT": "2018-11-20",
            "ANSWT": 6210000.00, "WAESSION": "USD",
            "IWERK": "FH01", "SWERK": "FH01", "STORT": "MTR_POOL_A",
            "TPLNR": "US-ARMY-III-1AD-2ABCT", "USTATUS": "FMC",
            "STATTEXT": "FULLY MISSION CAPABLE", "GEWRK": "MAINT_CO_A",
            "LIN_NUM": "M77A2B", "NSN": "2350-01-087-1095",
            "UIC": "W45XAA", "AEDAT": "2024-01-15", "AENAM": "SGT.JOHNSON",
        },
        {
            "EQUNR": "000000000010045232", "EQTYP": "V",
            "TXTMI": "M2A3 BRADLEY FIGHTING VEHICLE", "EQART": "TRACKED_VH",
            "INBDT": "2020-06-22", "HERST": "BAE SYSTEMS",
            "SERGE": "BAE-2020-7821", "ANSDT": "2020-01-15",
            "ANSWT": 3200000.00, "WAESSION": "USD",
            "IWERK": "FH01", "SWERK": "FH01", "STORT": "MTR_POOL_B",
            "TPLNR": "US-ARMY-III-1AD-2ABCT", "USTATUS": "PMC",
            "STATTEXT": "PARTIALLY MISSION CAPABLE", "GEWRK": "MAINT_CO_A",
            "LIN_NUM": "M62A3D", "NSN": "2350-01-579-2501",
            "UIC": "W45XAA", "AEDAT": "2024-01-14", "AENAM": "SPC.WILLIAMS",
        },
        {
            "EQUNR": "000000000010045240", "EQTYP": "V",
            "TXTMI": "M109A7 PALADIN HOWITZER", "EQART": "TRACKED_VH",
            "INBDT": "2021-09-10", "HERST": "BAE SYSTEMS",
            "SERGE": "BAE-2021-1102", "ANSDT": "2021-05-03",
            "ANSWT": 4800000.00, "WAESSION": "USD",
            "IWERK": "FH01", "SWERK": "FH01", "STORT": "MTR_POOL_C",
            "TPLNR": "US-ARMY-III-1AD-DIVARTY", "USTATUS": "FMC",
            "STATTEXT": "FULLY MISSION CAPABLE", "GEWRK": "MAINT_CO_B",
            "LIN_NUM": "M90A7E", "NSN": "2350-01-614-4321",
            "UIC": "W45XBB", "AEDAT": "2024-01-12", "AENAM": "SSG.CHEN",
        },
    ]

    result = migrate(SAMPLE_DATA)
    print(f"\n{'='*60}")
    print(f"  Migration Statistics")
    print(f"{'='*60}")
    for key, val in result["stats"].items():
        print(f"  {key:>15}: {val}")
    print(f"{'='*60}\n")

    for row in result["transformed"]:
        print(row)
