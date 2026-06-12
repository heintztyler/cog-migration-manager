"""
Tests for the GCSS-Army UNIT_READINESS -> ALERP readiness_reports migration.

Covers:
    - Happy-path transformation of all sample records
    - Field type correctness
    - Required-field validation
    - NULL / empty-string edge cases
    - Idempotent UUID generation
    - FMC rate recomputation
    - Equipment category normalisation
    - Date parsing for multiple formats
"""

import unittest
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from readiness_migration import (
    EQUIP_CAT_MAP,
    LEGACY_SYSTEM,
    migrate,
    transform_record,
    _compute_fmc_rate,
    _generate_report_uuid,
    _normalise_equip_cat,
    _parse_date,
    _safe_decimal,
    _safe_int,
    _validate_record,
)

SAMPLE_DATA = [
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


class TestTransformRecord(unittest.TestCase):
    """Tests for transform_record on the three sample rows."""

    def setUp(self):
        self.records = [transform_record(r) for r in SAMPLE_DATA]

    def test_all_target_fields_present(self):
        expected_keys = {
            "report_id", "legacy_system", "legacy_report_id", "uic",
            "unit_name", "report_date", "asset_category",
            "authorized_quantity", "on_hand_quantity", "fmc_quantity",
            "pmc_quantity", "nmc_quantity", "fmc_rate", "deadline_quantity",
            "commander_remarks", "created_at",
        }
        for rec in self.records:
            self.assertEqual(set(rec.keys()), expected_keys)

    def test_report_id_is_valid_uuid(self):
        for rec in self.records:
            uuid.UUID(rec["report_id"])  # raises on bad format

    def test_legacy_system_constant(self):
        for rec in self.records:
            self.assertEqual(rec["legacy_system"], LEGACY_SYSTEM)

    def test_legacy_report_id_preserved(self):
        self.assertEqual(self.records[0]["legacy_report_id"], "USR-2024-0115-1AD")
        self.assertEqual(self.records[2]["legacy_report_id"], "USR-2024-0115-DIV")

    def test_uic_mapped(self):
        self.assertEqual(self.records[0]["uic"], "W45XAA")
        self.assertEqual(self.records[2]["uic"], "W45XBB")

    def test_unit_name_mapped(self):
        self.assertEqual(self.records[0]["unit_name"], "2D ABCT, 1ST ARMORED DIV")

    def test_report_date_iso(self):
        for rec in self.records:
            datetime.strptime(rec["report_date"], "%Y-%m-%d")

    def test_asset_category_normalised(self):
        self.assertEqual(self.records[0]["asset_category"], "TRACKED_VEHICLE")
        self.assertEqual(self.records[1]["asset_category"], "WHEELED_VEHICLE")

    def test_integer_quantities(self):
        rec = self.records[0]
        self.assertIsInstance(rec["authorized_quantity"], int)
        self.assertIsInstance(rec["on_hand_quantity"], int)
        self.assertIsInstance(rec["fmc_quantity"], int)
        self.assertIsInstance(rec["pmc_quantity"], int)
        self.assertIsInstance(rec["nmc_quantity"], int)
        self.assertIsInstance(rec["deadline_quantity"], int)

    def test_fmc_rate_recomputed(self):
        # Record 0: 48/56 = 85.71%
        self.assertEqual(self.records[0]["fmc_rate"], "85.71")
        # Record 1: 218/240 = 90.83%
        self.assertEqual(self.records[1]["fmc_rate"], "90.83")
        # Record 2: 22/24 = 91.67%
        self.assertEqual(self.records[2]["fmc_rate"], "91.67")

    def test_commander_remarks_mapped(self):
        self.assertEqual(
            self.records[0]["commander_remarks"],
            "2x M1A2 AWAITING POWERPACK; ESD 30JAN",
        )

    def test_created_at_is_iso_timestamp(self):
        for rec in self.records:
            dt = datetime.fromisoformat(rec["created_at"])
            self.assertIsNotNone(dt.tzinfo)


class TestMigratePipeline(unittest.TestCase):
    """End-to-end tests for the migrate() function."""

    def setUp(self):
        self.result = migrate(SAMPLE_DATA)

    def test_all_records_succeed(self):
        self.assertEqual(self.result["total"], 3)
        self.assertEqual(self.result["succeeded"], 3)
        self.assertEqual(self.result["skipped"], 0)

    def test_no_errors(self):
        self.assertEqual(self.result["errors"], [])

    def test_transformed_count(self):
        self.assertEqual(len(self.result["transformed"]), 3)


class TestIdempotency(unittest.TestCase):
    """Deterministic UUIDs make re-runs produce identical IDs."""

    def test_same_input_same_uuid(self):
        u1 = _generate_report_uuid("USR-2024-0115-1AD", "TRACKED_VH")
        u2 = _generate_report_uuid("USR-2024-0115-1AD", "TRACKED_VH")
        self.assertEqual(u1, u2)

    def test_different_equip_cat_different_uuid(self):
        u1 = _generate_report_uuid("USR-2024-0115-1AD", "TRACKED_VH")
        u2 = _generate_report_uuid("USR-2024-0115-1AD", "WHEELED_VH")
        self.assertNotEqual(u1, u2)

    def test_migrate_twice_same_ids(self):
        r1 = migrate(SAMPLE_DATA)
        r2 = migrate(SAMPLE_DATA)
        ids1 = [r["report_id"] for r in r1["transformed"]]
        ids2 = [r["report_id"] for r in r2["transformed"]]
        self.assertEqual(ids1, ids2)


class TestValidation(unittest.TestCase):
    """Validation logic for required fields and quantity checks."""

    def test_missing_report_id(self):
        record = {
            "UIC": "W45XAA", "REPORT_DATE": "2024-01-15",
            "EQUIP_CAT": "TRACKED_VH", "AUTH_QTY": 10, "ON_HAND": 10, "FMC_QTY": 8,
        }
        errors = _validate_record(record, 0)
        self.assertTrue(any("REPORT_ID" in e for e in errors))

    def test_empty_uic(self):
        record = {
            "REPORT_ID": "X", "UIC": "", "REPORT_DATE": "2024-01-15",
            "EQUIP_CAT": "TRACKED_VH", "AUTH_QTY": 10, "ON_HAND": 10, "FMC_QTY": 8,
        }
        errors = _validate_record(record, 0)
        self.assertTrue(any("UIC" in e for e in errors))

    def test_negative_quantity_flagged(self):
        record = {
            "REPORT_ID": "X", "UIC": "Y", "REPORT_DATE": "2024-01-15",
            "EQUIP_CAT": "TRACKED_VH", "AUTH_QTY": -1, "ON_HAND": 10, "FMC_QTY": 8,
        }
        errors = _validate_record(record, 0)
        self.assertTrue(any("quantity" in e for e in errors))

    def test_valid_record_no_errors(self):
        errors = _validate_record(SAMPLE_DATA[0], 0)
        self.assertEqual(errors, [])

    def test_skipped_records_counted(self):
        bad = {"UIC": "X", "REPORT_DATE": "2024-01-15", "EQUIP_CAT": "TRACKED_VH"}
        result = migrate([bad, SAMPLE_DATA[0]])
        self.assertEqual(result["skipped"], 1)
        self.assertEqual(result["succeeded"], 1)


class TestEquipCatNormalisation(unittest.TestCase):
    def test_all_known_categories(self):
        for legacy, expected in EQUIP_CAT_MAP.items():
            self.assertEqual(_normalise_equip_cat(legacy), expected)

    def test_unknown_passthrough(self):
        self.assertEqual(_normalise_equip_cat("NEW_CAT"), "NEW_CAT")

    def test_case_insensitive(self):
        self.assertEqual(_normalise_equip_cat("tracked_vh"), "TRACKED_VEHICLE")

    def test_none_returns_unknown(self):
        self.assertEqual(_normalise_equip_cat(None), "UNKNOWN")

    def test_empty_returns_unknown(self):
        self.assertEqual(_normalise_equip_cat(""), "UNKNOWN")


class TestDateParsing(unittest.TestCase):
    def test_iso_format(self):
        self.assertEqual(_parse_date("2024-01-15"), "2024-01-15")

    def test_sap_compact(self):
        self.assertEqual(_parse_date("20240115"), "2024-01-15")

    def test_european_format(self):
        self.assertEqual(_parse_date("15.01.2024"), "2024-01-15")

    def test_us_format(self):
        self.assertEqual(_parse_date("01/15/2024"), "2024-01-15")

    def test_none(self):
        self.assertIsNone(_parse_date(None))

    def test_empty_string(self):
        self.assertIsNone(_parse_date(""))


class TestNullEdgeCases(unittest.TestCase):
    def test_null_remarks_becomes_none(self):
        record = {
            "REPORT_ID": "T1", "UIC": "W45XAA", "REPORT_DATE": "2024-01-15",
            "EQUIP_CAT": "TRACKED_VH", "AUTH_QTY": 10, "ON_HAND": 10,
            "FMC_QTY": 8, "PMC_QTY": 1, "NMC_QTY": 1, "FMC_RATE": 80.00,
            "DEADLINE_QTY": 0, "REMARKS": None,
        }
        row = transform_record(record)
        self.assertIsNone(row["commander_remarks"])

    def test_empty_remarks_becomes_none(self):
        record = {
            "REPORT_ID": "T2", "UIC": "W45XAA", "REPORT_DATE": "2024-01-15",
            "EQUIP_CAT": "TRACKED_VH", "AUTH_QTY": 10, "ON_HAND": 10,
            "FMC_QTY": 8, "PMC_QTY": 1, "NMC_QTY": 1, "FMC_RATE": 80.00,
            "DEADLINE_QTY": 0, "REMARKS": "   ",
        }
        row = transform_record(record)
        self.assertIsNone(row["commander_remarks"])

    def test_missing_optional_int_defaults_to_zero(self):
        record = {
            "REPORT_ID": "T3", "UIC": "W45XAA", "REPORT_DATE": "2024-01-15",
            "EQUIP_CAT": "TRACKED_VH", "AUTH_QTY": 10, "ON_HAND": 10, "FMC_QTY": 8,
        }
        row = transform_record(record)
        self.assertEqual(row["pmc_quantity"], 0)
        self.assertEqual(row["deadline_quantity"], 0)


class TestSafeInt(unittest.TestCase):
    def test_int_value(self):
        self.assertEqual(_safe_int(42), 42)

    def test_string_int(self):
        self.assertEqual(_safe_int("58"), 58)

    def test_none_default(self):
        self.assertEqual(_safe_int(None), 0)

    def test_none_custom_default(self):
        self.assertEqual(_safe_int(None, -1), -1)

    def test_invalid_string(self):
        self.assertEqual(_safe_int("abc"), 0)


class TestSafeDecimal(unittest.TestCase):
    def test_float_value(self):
        self.assertEqual(_safe_decimal(85.71), "85.71")

    def test_string_value(self):
        self.assertEqual(_safe_decimal("91.67"), "91.67")

    def test_none_default(self):
        self.assertEqual(_safe_decimal(None), "0.00")

    def test_invalid_default(self):
        self.assertEqual(_safe_decimal("abc"), "0.00")


class TestComputeFmcRate(unittest.TestCase):
    def test_recompute_from_quantities(self):
        self.assertEqual(_compute_fmc_rate(48, 56, 85.71), "85.71")

    def test_zero_on_hand_falls_back(self):
        self.assertEqual(_compute_fmc_rate(0, 0, 50.00), "50.00")

    def test_full_rate(self):
        self.assertEqual(_compute_fmc_rate(10, 10, 100.00), "100.00")


if __name__ == "__main__":
    unittest.main()
