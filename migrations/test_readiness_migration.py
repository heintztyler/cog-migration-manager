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

    def test_quantity_values(self):
        rec = self.records[0]
        self.assertEqual(rec["authorized_quantity"], 58)
        self.assertEqual(rec["on_hand_quantity"], 56)
        self.assertEqual(rec["fmc_quantity"], 48)
        self.assertEqual(rec["pmc_quantity"], 5)
        self.assertEqual(rec["nmc_quantity"], 3)
        self.assertEqual(rec["deadline_quantity"], 2)


class TestIdempotency(unittest.TestCase):
    """UUID generation must be deterministic on repeated runs."""

    def test_same_input_same_uuid(self):
        rec1 = transform_record(SAMPLE_DATA[0])
        rec2 = transform_record(SAMPLE_DATA[0])
        self.assertEqual(rec1["report_id"], rec2["report_id"])

    def test_different_equip_cat_different_uuid(self):
        rec1 = transform_record(SAMPLE_DATA[0])  # TRACKED_VH
        rec2 = transform_record(SAMPLE_DATA[1])  # WHEELED_VH
        self.assertNotEqual(rec1["report_id"], rec2["report_id"])


class TestMigrateFunction(unittest.TestCase):
    """Integration tests for the migrate() pipeline."""

    def test_all_records_succeed(self):
        result = migrate(SAMPLE_DATA)
        self.assertEqual(result["total"], 3)
        self.assertEqual(result["succeeded"], 3)
        self.assertEqual(result["skipped"], 0)
        self.assertEqual(result["errors"], [])

    def test_transformed_count(self):
        result = migrate(SAMPLE_DATA)
        self.assertEqual(len(result["transformed"]), 3)

    def test_empty_input(self):
        result = migrate([])
        self.assertEqual(result["total"], 0)
        self.assertEqual(result["succeeded"], 0)
        self.assertEqual(result["skipped"], 0)


class TestValidation(unittest.TestCase):
    """Validation catches missing / invalid required fields."""

    def test_missing_report_id(self):
        bad = {
            "UIC": "W45XAA",
            "REPORT_DATE": "2024-01-15",
            "EQUIP_CAT": "TRACKED_VH",
            "AUTH_QTY": 10,
            "ON_HAND": 10,
            "FMC_QTY": 10,
        }
        errors = _validate_record(bad, 0)
        self.assertTrue(any("REPORT_ID" in e for e in errors))

    def test_missing_uic(self):
        bad = {
            "REPORT_ID": "R1",
            "REPORT_DATE": "2024-01-15",
            "EQUIP_CAT": "TRACKED_VH",
            "AUTH_QTY": 10,
            "ON_HAND": 10,
            "FMC_QTY": 10,
        }
        errors = _validate_record(bad, 0)
        self.assertTrue(any("UIC" in e for e in errors))

    def test_empty_string_report_id(self):
        bad = {
            "REPORT_ID": "",
            "UIC": "W45XAA",
            "REPORT_DATE": "2024-01-15",
            "EQUIP_CAT": "TRACKED_VH",
            "AUTH_QTY": 10,
            "ON_HAND": 10,
            "FMC_QTY": 10,
        }
        errors = _validate_record(bad, 0)
        self.assertTrue(any("REPORT_ID" in e for e in errors))

    def test_invalid_record_skipped_in_migrate(self):
        bad_records = [
            {"UIC": "W45XAA"},  # missing REPORT_ID, REPORT_DATE, EQUIP_CAT
        ]
        result = migrate(bad_records)
        self.assertEqual(result["succeeded"], 0)
        self.assertEqual(result["skipped"], 1)
        self.assertGreater(len(result["errors"]), 0)


class TestEdgeCases(unittest.TestCase):
    """NULL values, empty strings, and unusual inputs."""

    def _valid_base(self, **overrides):
        base = {
            "REPORT_ID": "TEST-001",
            "UIC": "W00AAA",
            "UNIT_NAME": "TEST UNIT",
            "REPORT_DATE": "2024-06-01",
            "EQUIP_CAT": "TRACKED_VH",
            "AUTH_QTY": 10,
            "ON_HAND": 10,
            "FMC_QTY": 8,
            "PMC_QTY": 1,
            "NMC_QTY": 1,
            "FMC_RATE": 80.00,
            "DEADLINE_QTY": 0,
            "REMARKS": "",
        }
        base.update(overrides)
        return base

    def test_none_remarks(self):
        rec = transform_record(self._valid_base(REMARKS=None))
        self.assertIsNone(rec["commander_remarks"])

    def test_empty_remarks(self):
        rec = transform_record(self._valid_base(REMARKS=""))
        self.assertIsNone(rec["commander_remarks"])

    def test_none_unit_name(self):
        rec = transform_record(self._valid_base(UNIT_NAME=None))
        self.assertIsNone(rec["unit_name"])

    def test_zero_on_hand_fmc_rate(self):
        rec = transform_record(self._valid_base(ON_HAND=0, FMC_QTY=0, FMC_RATE=0.0))
        self.assertEqual(rec["fmc_rate"], "0.00")

    def test_none_quantities_default_to_zero(self):
        rec = transform_record(self._valid_base(
            AUTH_QTY=None, ON_HAND=None, FMC_QTY=None,
            PMC_QTY=None, NMC_QTY=None, DEADLINE_QTY=None,
        ))
        self.assertEqual(rec["authorized_quantity"], 0)
        self.assertEqual(rec["on_hand_quantity"], 0)
        self.assertEqual(rec["fmc_quantity"], 0)
        self.assertEqual(rec["pmc_quantity"], 0)
        self.assertEqual(rec["nmc_quantity"], 0)
        self.assertEqual(rec["deadline_quantity"], 0)

    def test_string_quantity_coerced(self):
        rec = transform_record(self._valid_base(AUTH_QTY="42"))
        self.assertEqual(rec["authorized_quantity"], 42)

    def test_unknown_equip_cat_passed_through(self):
        rec = transform_record(self._valid_base(EQUIP_CAT="NEW_CAT_XYZ"))
        self.assertEqual(rec["asset_category"], "NEW_CAT_XYZ")


class TestHelperFunctions(unittest.TestCase):
    """Unit tests for individual helper functions."""

    def test_safe_int_none(self):
        self.assertEqual(_safe_int(None), 0)

    def test_safe_int_string(self):
        self.assertEqual(_safe_int("123"), 123)

    def test_safe_int_invalid(self):
        self.assertEqual(_safe_int("abc"), 0)

    def test_safe_decimal_none(self):
        self.assertEqual(_safe_decimal(None), "0.00")

    def test_safe_decimal_precision(self):
        self.assertEqual(_safe_decimal(85.714), "85.71")

    def test_safe_decimal_string(self):
        self.assertEqual(_safe_decimal("91.666"), "91.67")

    def test_parse_date_iso(self):
        self.assertEqual(_parse_date("2024-01-15"), "2024-01-15")

    def test_parse_date_compact(self):
        self.assertEqual(_parse_date("20240115"), "2024-01-15")

    def test_parse_date_dot(self):
        self.assertEqual(_parse_date("15.01.2024"), "2024-01-15")

    def test_parse_date_us(self):
        self.assertEqual(_parse_date("01/15/2024"), "2024-01-15")

    def test_parse_date_none(self):
        self.assertIsNone(_parse_date(None))

    def test_parse_date_empty(self):
        self.assertIsNone(_parse_date(""))

    def test_normalise_equip_cat_known(self):
        self.assertEqual(_normalise_equip_cat("TRACKED_VH"), "TRACKED_VEHICLE")

    def test_normalise_equip_cat_unknown(self):
        self.assertEqual(_normalise_equip_cat("FUTURE_SYS"), "FUTURE_SYS")

    def test_normalise_equip_cat_none(self):
        self.assertEqual(_normalise_equip_cat(None), "UNKNOWN")

    def test_normalise_equip_cat_whitespace(self):
        self.assertEqual(_normalise_equip_cat("  tracked_vh  "), "TRACKED_VEHICLE")

    def test_compute_fmc_rate_normal(self):
        self.assertEqual(_compute_fmc_rate(48, 56, 85.71), "85.71")

    def test_compute_fmc_rate_zero_on_hand(self):
        self.assertEqual(_compute_fmc_rate(0, 0, 50.00), "50.00")

    def test_generate_report_uuid_deterministic(self):
        u1 = _generate_report_uuid("R1", "TRACKED_VH")
        u2 = _generate_report_uuid("R1", "TRACKED_VH")
        self.assertEqual(u1, u2)

    def test_generate_report_uuid_varies(self):
        u1 = _generate_report_uuid("R1", "TRACKED_VH")
        u2 = _generate_report_uuid("R1", "WHEELED_VH")
        self.assertNotEqual(u1, u2)


if __name__ == "__main__":
    unittest.main()
