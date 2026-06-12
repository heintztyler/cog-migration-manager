"""
Tests for GCSS-Army AUFK_WORKORDER → ALERP maintenance_orders migration.

Validates field mapping, type correctness, edge cases, and idempotency.
"""

import uuid
import sys
import os
from datetime import datetime
from decimal import Decimal

# Ensure the migrations directory is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from importlib import import_module

# Import with hyphenated filename
migration = import_module("maintenance-orders_migration")


# --- Sample Data ---

SAMPLE_RECORDS = migration.SAMPLE_SOURCE_DATA

RECORD_SCHEDULED = SAMPLE_RECORDS[0]  # PM01, EXEC phase
RECORD_UNSCHEDULED = SAMPLE_RECORDS[1]  # PM02, WAIT phase
RECORD_ANNUAL = SAMPLE_RECORDS[2]  # PM03, PLAN phase


# --- Test Helpers ---


def assert_eq(actual, expected, msg=""):
    if actual != expected:
        raise AssertionError(f"{msg}: expected {expected!r}, got {actual!r}")


def assert_is_none(value, msg=""):
    if value is not None:
        raise AssertionError(f"{msg}: expected None, got {value!r}")


def assert_is_not_none(value, msg=""):
    if value is None:
        raise AssertionError(f"{msg}: unexpected None")


def assert_true(value, msg=""):
    if not value:
        raise AssertionError(f"{msg}: expected truthy, got {value!r}")


def assert_in(item, collection, msg=""):
    if item not in collection:
        raise AssertionError(f"{msg}: {item!r} not in {collection!r}")


# --- Test: Full Migration Run ---


def test_run_migration_basic():
    """Test that run_migration processes all sample records successfully."""
    result = migration.run_migration(SAMPLE_RECORDS)
    stats = result["statistics"]

    assert_eq(stats["total_source_records"], 3, "total source")
    assert_eq(stats["successfully_transformed"], 3, "transformed count")
    assert_eq(stats["skipped"], 0, "skipped count")
    assert_eq(len(result["records"]), 3, "output record count")


# --- Test: Field Mapping ---


def test_order_id_is_valid_uuid():
    """Each transformed record has a valid UUID order_id."""
    result = migration.run_migration(SAMPLE_RECORDS)
    for rec in result["records"]:
        parsed = uuid.UUID(rec["order_id"])
        assert_eq(parsed.version, 5, "UUID version")


def test_order_id_is_deterministic():
    """Same source AUFNR always produces same order_id (idempotency)."""
    r1 = migration.run_migration(SAMPLE_RECORDS)
    r2 = migration.run_migration(SAMPLE_RECORDS)
    for a, b in zip(r1["records"], r2["records"]):
        assert_eq(a["order_id"], b["order_id"], "deterministic UUID")


def test_legacy_system_field():
    """legacy_system is always GCSS_ARMY."""
    result = migration.run_migration(SAMPLE_RECORDS)
    for rec in result["records"]:
        assert_eq(rec["legacy_system"], "GCSS_ARMY", "legacy_system")


def test_legacy_order_number_stripped():
    """legacy_order_number has leading zeros stripped."""
    result = migration.run_migration(SAMPLE_RECORDS)
    assert_eq(result["records"][0]["legacy_order_number"], "4521001")
    assert_eq(result["records"][1]["legacy_order_number"], "4521002")
    assert_eq(result["records"][2]["legacy_order_number"], "4521003")


def test_order_type_mapping():
    """AUART maps to correct order_type enum values."""
    result = migration.run_migration(SAMPLE_RECORDS)
    assert_eq(result["records"][0]["order_type"], "SCHEDULED")
    assert_eq(result["records"][1]["order_type"], "UNSCHEDULED")
    assert_eq(result["records"][2]["order_type"], "ANNUAL_SERVICE")


def test_title_is_title_cased():
    """KTEXT is converted to title case."""
    result = migration.run_migration(SAMPLE_RECORDS)
    assert_eq(result["records"][0]["title"], "Scheduled Maint - Engine Overhaul")
    assert_eq(result["records"][1]["title"], "Unscheduled - Transmission Fault")


def test_priority_mapping():
    """PRIESSION maps to integer priority."""
    result = migration.run_migration(SAMPLE_RECORDS)
    assert_eq(result["records"][0]["priority"], 2)  # HIGH
    assert_eq(result["records"][1]["priority"], 1)  # URGENT
    assert_eq(result["records"][2]["priority"], 3)  # ROUTINE


def test_status_mapping_from_iphas():
    """IPHAS phase maps to ALERP status enum."""
    result = migration.run_migration(SAMPLE_RECORDS)
    assert_eq(result["records"][0]["status"], "IN_PROGRESS")  # EXEC
    assert_eq(result["records"][1]["status"], "AWAITING_PARTS")  # WAIT
    assert_eq(result["records"][2]["status"], "PLANNED")  # PLAN


def test_date_fields():
    """Date fields are correctly parsed to ISO format."""
    result = migration.run_migration(SAMPLE_RECORDS)
    rec = result["records"][0]
    assert_eq(rec["scheduled_start"], "2024-02-01")
    assert_eq(rec["scheduled_end"], "2024-02-15")


def test_created_at_is_timestamp():
    """created_at is a valid ISO timestamp with timezone."""
    result = migration.run_migration(SAMPLE_RECORDS)
    rec = result["records"][0]
    assert_true("+00:00" in rec["created_at"], "has timezone")
    assert_true(rec["created_at"].startswith("2024-01-20"), "correct date")


def test_created_by_format():
    """ERNAM is lowercased with @army.mil appended."""
    result = migration.run_migration(SAMPLE_RECORDS)
    assert_eq(result["records"][0]["created_by"], "cw3.martinez@army.mil")
    assert_eq(result["records"][1]["created_by"], "sfc.thompson@army.mil")


def test_decimal_fields():
    """MAN_HOURS and ACT_HOURS are Decimal values."""
    result = migration.run_migration(SAMPLE_RECORDS)
    rec = result["records"][0]
    assert_eq(rec["estimated_hours"], Decimal("240.0"))
    assert_eq(rec["actual_hours"], Decimal("186.5"))


def test_fault_code_mapping():
    """FAULT_CODE is passed through or set to None if empty."""
    result = migration.run_migration(SAMPLE_RECORDS)
    assert_eq(result["records"][0]["fault_code"], "ENG-0042")
    assert_eq(result["records"][1]["fault_code"], "TRN-0018")
    assert_is_none(result["records"][2]["fault_code"])


def test_asset_id_generated():
    """asset_id is a deterministic UUID generated from EQUNR."""
    result = migration.run_migration(SAMPLE_RECORDS)
    for rec in result["records"]:
        assert_is_not_none(rec["asset_id"], "asset_id present")
        parsed = uuid.UUID(rec["asset_id"])
        assert_eq(parsed.version, 5, "asset UUID version")


def test_work_center_mapping():
    """ARBPL maps directly to work_center."""
    result = migration.run_migration(SAMPLE_RECORDS)
    assert_eq(result["records"][0]["work_center"], "MAINT_3A")
    assert_eq(result["records"][1]["work_center"], "MAINT_2B")


def test_cost_center_mapping():
    """KOSTL maps directly to cost_center."""
    result = migration.run_migration(SAMPLE_RECORDS)
    assert_eq(result["records"][0]["cost_center"], "CC-1AD-MNT")


def test_owning_uic_extracted():
    """owning_uic is derived from TPLNR functional location."""
    result = migration.run_migration(SAMPLE_RECORDS)
    # US-ARMY-III-1AD-2ABCT → last segment "2ABCT"
    assert_eq(result["records"][0]["owning_uic"], "2ABCT")


# --- Test: Edge Cases ---


def test_missing_aufnr_skipped():
    """Records with missing AUFNR are skipped."""
    records = [{"AUTYP": "PM", "AUART": "PM01", "KTEXT": "TEST"}]
    result = migration.run_migration(records)
    assert_eq(result["statistics"]["skipped"], 1)
    assert_eq(len(result["records"]), 0)


def test_empty_aufnr_skipped():
    """Records with empty string AUFNR are skipped."""
    records = [{"AUFNR": "", "AUTYP": "PM", "AUART": "PM01"}]
    result = migration.run_migration(records)
    assert_eq(result["statistics"]["skipped"], 1)


def test_null_optional_fields():
    """NULL/None optional fields are handled gracefully."""
    record = {
        "AUFNR": "000099999999",
        "AUTYP": "PM",
        "AUART": None,
        "KTEXT": None,
        "EQUNR": None,
        "TPLNR": None,
        "PRIESSION": None,
        "GSTRP": None,
        "GLTRP": None,
        "ERDAT": None,
        "ERNAM": None,
        "ARBPL": None,
        "IPHAS": None,
        "KOSTL": None,
        "OVERALL_STAT": None,
        "MAN_HOURS": None,
        "ACT_HOURS": None,
        "FAULT_CODE": None,
    }
    result = migration.run_migration([record])
    assert_eq(result["statistics"]["successfully_transformed"], 1)
    rec = result["records"][0]
    assert_eq(rec["order_type"], "SCHEDULED")  # default
    assert_eq(rec["title"], "Untitled Maintenance Order")
    assert_is_none(rec["asset_id"])
    assert_is_none(rec["owning_uic"])
    assert_eq(rec["priority"], 3)  # default ROUTINE
    assert_eq(rec["status"], "CREATED")  # default
    assert_is_none(rec["scheduled_start"])
    assert_is_none(rec["scheduled_end"])
    assert_is_none(rec["estimated_hours"])
    assert_is_none(rec["actual_hours"])
    assert_is_none(rec["fault_code"])
    assert_eq(rec["created_by"], "system@army.mil")


def test_empty_string_fields():
    """Empty string fields are treated as NULL."""
    record = {
        "AUFNR": "000088888888",
        "AUTYP": "PM",
        "AUART": "",
        "KTEXT": "   ",
        "EQUNR": "   ",
        "TPLNR": "",
        "PRIESSION": "",
        "GSTRP": "",
        "GLTRP": "",
        "ERDAT": "",
        "ERNAM": "  ",
        "ARBPL": "",
        "IPHAS": "",
        "KOSTL": "",
        "OVERALL_STAT": "",
        "MAN_HOURS": None,
        "ACT_HOURS": None,
        "FAULT_CODE": "",
    }
    result = migration.run_migration([record])
    rec = result["records"][0]
    assert_eq(rec["title"], "Untitled Maintenance Order")
    assert_is_none(rec["asset_id"])
    assert_is_none(rec["work_center"])
    assert_is_none(rec["fault_code"])


def test_sap_compact_date_format():
    """Handles YYYYMMDD compact date format from SAP."""
    date_result = migration.parse_date("20240201")
    assert_eq(date_result, "2024-02-01")


def test_invalid_date_returns_none():
    """Invalid date strings return None."""
    assert_is_none(migration.parse_date("not-a-date"))
    assert_is_none(migration.parse_date("99999999"))
    assert_is_none(migration.parse_date("2024-13-01"))


def test_unknown_order_type_defaults():
    """Unknown AUART defaults to SCHEDULED."""
    assert_eq(migration.map_order_type("PM99"), "SCHEDULED")
    assert_eq(migration.map_order_type("ZZZZ"), "SCHEDULED")


def test_priority_out_of_range_defaults():
    """Priority values outside 1-3 default to 3 (ROUTINE)."""
    assert_eq(migration.map_priority("0"), 3)
    assert_eq(migration.map_priority("5"), 3)
    assert_eq(migration.map_priority("abc"), 3)


def test_updated_at_is_populated():
    """updated_at is always populated with current timestamp."""
    result = migration.run_migration(SAMPLE_RECORDS)
    for rec in result["records"]:
        assert_is_not_none(rec["updated_at"], "updated_at present")


def test_actual_start_end_are_none():
    """actual_start and actual_end are None (not in source)."""
    result = migration.run_migration(SAMPLE_RECORDS)
    for rec in result["records"]:
        assert_is_none(rec["actual_start"])
        assert_is_none(rec["actual_end"])


# --- Test: Type Correctness ---


def test_output_types():
    """Verify correct Python types for all output fields."""
    result = migration.run_migration(SAMPLE_RECORDS)
    rec = result["records"][0]

    assert_true(isinstance(rec["order_id"], str), "order_id is str")
    assert_true(isinstance(rec["legacy_system"], str), "legacy_system is str")
    assert_true(isinstance(rec["legacy_order_number"], str), "legacy_order_number is str")
    assert_true(isinstance(rec["order_type"], str), "order_type is str")
    assert_true(isinstance(rec["title"], str), "title is str")
    assert_true(isinstance(rec["priority"], int), "priority is int")
    assert_true(isinstance(rec["status"], str), "status is str")
    assert_true(isinstance(rec["created_at"], str), "created_at is str")
    assert_true(isinstance(rec["created_by"], str), "created_by is str")
    assert_true(isinstance(rec["updated_at"], str), "updated_at is str")
    assert_true(isinstance(rec["estimated_hours"], Decimal), "estimated_hours is Decimal")
    assert_true(isinstance(rec["actual_hours"], Decimal), "actual_hours is Decimal")


def test_all_required_fields_present():
    """All target schema fields are present in output records."""
    required_fields = [
        "order_id", "legacy_system", "legacy_order_number", "asset_id",
        "order_type", "title", "description", "priority", "status",
        "owning_uic", "work_center", "scheduled_start", "scheduled_end",
        "actual_start", "actual_end", "estimated_hours", "actual_hours",
        "fault_code", "cost_center", "created_at", "created_by", "updated_at",
    ]
    result = migration.run_migration(SAMPLE_RECORDS)
    for rec in result["records"]:
        for field in required_fields:
            assert_true(field in rec, f"field {field} present")


# --- Test Runner ---


def run_tests():
    """Run all test functions and report results."""
    test_functions = [
        v for k, v in globals().items()
        if k.startswith("test_") and callable(v)
    ]

    passed = 0
    failed = 0
    errors = []

    print(f"\nRunning {len(test_functions)} tests...\n")

    for test_fn in sorted(test_functions, key=lambda f: f.__name__):
        try:
            test_fn()
            passed += 1
            print(f"  PASS  {test_fn.__name__}")
        except (AssertionError, Exception) as e:
            failed += 1
            errors.append((test_fn.__name__, str(e)))
            print(f"  FAIL  {test_fn.__name__}: {e}")

    print(f"\n{'=' * 60}")
    print(f"Results: {passed} passed, {failed} failed, {len(test_functions)} total")
    print(f"{'=' * 60}")

    if errors:
        print("\nFailures:")
        for name, err in errors:
            print(f"  - {name}: {err}")
        return 1
    return 0


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
