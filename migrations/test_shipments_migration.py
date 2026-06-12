"""
Tests for LMP SHIPMENT_TRACKING → ALERP shipments migration.

Validates field mapping, type correctness, edge-case handling, and
idempotency of the transformation logic.
"""

import unittest
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from shipments_migration import (
    LEGACY_SYSTEM,
    MigrationStats,
    ValidationError,
    generate_item_id,
    generate_procurement_order_id,
    generate_shipment_id,
    map_shipment_type,
    map_status,
    parse_date,
    parse_decimal,
    run_migration,
    transform_record,
    validate_record,
)

FIXED_TIMESTAMP = "2024-06-01T12:00:00+00:00"

SAMPLE_RECORD_1 = {
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
}

SAMPLE_RECORD_2 = {
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
}


class TestFieldMapping(unittest.TestCase):
    """Verify every source field maps to the correct target field."""

    def setUp(self):
        self.result = transform_record(SAMPLE_RECORD_1, now=FIXED_TIMESTAMP)

    def test_shipment_id_is_valid_uuid(self):
        uuid.UUID(self.result["shipment_id"])

    def test_legacy_system(self):
        self.assertEqual(self.result["legacy_system"], "LMP")

    def test_legacy_shipment_id(self):
        self.assertEqual(self.result["legacy_shipment_id"], "SHP-00891234")

    def test_tcn(self):
        self.assertEqual(self.result["tcn"], "W45G09-4108-0001")

    def test_shipment_type(self):
        self.assertEqual(self.result["shipment_type"], "SURFACE")

    def test_origin_dodaac(self):
        self.assertEqual(self.result["origin_dodaac"], "W45G09")

    def test_origin_name(self):
        self.assertEqual(self.result["origin_name"], "ANNISTON ARMY DEPOT")

    def test_destination_dodaac(self):
        self.assertEqual(self.result["destination_dodaac"], "W45XAA")

    def test_destination_name(self):
        self.assertEqual(self.result["destination_name"], "2ABCT, 1AD - FORT BLISS")

    def test_item_id_is_valid_uuid(self):
        uuid.UUID(self.result["item_id"])

    def test_procurement_order_id_is_valid_uuid(self):
        uuid.UUID(self.result["procurement_order_id"])

    def test_quantity(self):
        self.assertEqual(self.result["quantity"], Decimal("100.0"))

    def test_weight_lbs(self):
        self.assertEqual(self.result["weight_lbs"], Decimal("245.0"))

    def test_ship_date(self):
        self.assertEqual(self.result["ship_date"], "2024-01-10")

    def test_estimated_arrival(self):
        self.assertEqual(self.result["estimated_arrival"], "2024-01-17")

    def test_actual_arrival_null_for_in_transit(self):
        self.assertIsNone(self.result["actual_arrival"])

    def test_carrier(self):
        self.assertEqual(self.result["carrier"], "DLA DISTRIBUTION")

    def test_status_in_transit(self):
        self.assertEqual(self.result["status"], "IN_TRANSIT")

    def test_hazmat_class(self):
        self.assertEqual(self.result["hazmat_class"], "NONE")

    def test_created_at(self):
        self.assertEqual(self.result["created_at"], FIXED_TIMESTAMP)

    def test_updated_at(self):
        self.assertEqual(self.result["updated_at"], FIXED_TIMESTAMP)


class TestDeliveredRecord(unittest.TestCase):
    """Verify a delivered shipment with actual_arrival populated."""

    def setUp(self):
        self.result = transform_record(SAMPLE_RECORD_2, now=FIXED_TIMESTAMP)

    def test_status_delivered(self):
        self.assertEqual(self.result["status"], "DELIVERED")

    def test_actual_arrival_populated(self):
        self.assertEqual(self.result["actual_arrival"], "2024-01-14")

    def test_different_destination(self):
        self.assertEqual(self.result["destination_dodaac"], "W45XBB")
        self.assertEqual(self.result["destination_name"], "DIVARTY, 1AD - FORT BLISS")


class TestTypeCorrectness(unittest.TestCase):
    """Ensure output values have the correct Python types."""

    def setUp(self):
        self.result = transform_record(SAMPLE_RECORD_1, now=FIXED_TIMESTAMP)

    def test_string_fields(self):
        string_fields = [
            "shipment_id", "legacy_system", "legacy_shipment_id", "tcn",
            "shipment_type", "origin_dodaac", "origin_name",
            "destination_dodaac", "destination_name", "carrier",
            "status", "hazmat_class", "created_at", "updated_at",
        ]
        for field in string_fields:
            self.assertIsInstance(
                self.result[field], str, f"{field} should be str"
            )

    def test_uuid_fields(self):
        for field in ["shipment_id", "item_id", "procurement_order_id"]:
            val = self.result[field]
            if val is not None:
                uuid.UUID(val)  # raises on invalid

    def test_decimal_fields(self):
        for field in ["quantity", "weight_lbs"]:
            self.assertIsInstance(
                self.result[field], Decimal, f"{field} should be Decimal"
            )

    def test_date_fields_are_strings_or_none(self):
        for field in ["ship_date", "estimated_arrival", "actual_arrival"]:
            val = self.result[field]
            if val is not None:
                self.assertIsInstance(val, str)
                datetime.strptime(val, "%Y-%m-%d")


class TestRequiredFieldsPopulated(unittest.TestCase):
    """Every transformed record must have non-null required fields."""

    REQUIRED_FIELDS = [
        "shipment_id", "legacy_system", "legacy_shipment_id",
        "shipment_type", "status", "created_at", "updated_at",
    ]

    def test_required_fields_record_1(self):
        result = transform_record(SAMPLE_RECORD_1, now=FIXED_TIMESTAMP)
        for field in self.REQUIRED_FIELDS:
            self.assertIsNotNone(result[field], f"{field} must not be None")

    def test_required_fields_record_2(self):
        result = transform_record(SAMPLE_RECORD_2, now=FIXED_TIMESTAMP)
        for field in self.REQUIRED_FIELDS:
            self.assertIsNotNone(result[field], f"{field} must not be None")


class TestIdempotency(unittest.TestCase):
    """Same input must produce same output on repeated runs."""

    def test_deterministic_shipment_id(self):
        id1 = generate_shipment_id("SHP-00891234")
        id2 = generate_shipment_id("SHP-00891234")
        self.assertEqual(id1, id2)

    def test_deterministic_item_id(self):
        id1 = generate_item_id("000000000050012345", "2940-01-576-4108")
        id2 = generate_item_id("000000000050012345", "2940-01-576-4108")
        self.assertEqual(id1, id2)

    def test_deterministic_po_id(self):
        id1 = generate_procurement_order_id("4500089231")
        id2 = generate_procurement_order_id("4500089231")
        self.assertEqual(id1, id2)

    def test_full_transform_idempotent(self):
        r1 = transform_record(SAMPLE_RECORD_1, now=FIXED_TIMESTAMP)
        r2 = transform_record(SAMPLE_RECORD_1, now=FIXED_TIMESTAMP)
        self.assertEqual(r1, r2)

    def test_different_records_different_ids(self):
        id1 = generate_shipment_id("SHP-00891234")
        id2 = generate_shipment_id("SHP-00891200")
        self.assertNotEqual(id1, id2)


class TestNullAndEmptyHandling(unittest.TestCase):
    """Verify graceful handling of NULL/empty/missing values."""

    def _make_record(self, **overrides):
        base = dict(SAMPLE_RECORD_1)
        base.update(overrides)
        return base

    def test_null_actual_arrival(self):
        result = transform_record(
            self._make_record(ACTUAL_ARRIVAL=None), now=FIXED_TIMESTAMP,
        )
        self.assertIsNone(result["actual_arrival"])

    def test_empty_string_actual_arrival(self):
        result = transform_record(
            self._make_record(ACTUAL_ARRIVAL=""), now=FIXED_TIMESTAMP,
        )
        self.assertIsNone(result["actual_arrival"])

    def test_null_carrier(self):
        result = transform_record(
            self._make_record(CARRIER=None), now=FIXED_TIMESTAMP,
        )
        self.assertIsNone(result["carrier"])

    def test_empty_carrier(self):
        result = transform_record(
            self._make_record(CARRIER=""), now=FIXED_TIMESTAMP,
        )
        self.assertIsNone(result["carrier"])

    def test_null_tcn(self):
        result = transform_record(
            self._make_record(TCN=None), now=FIXED_TIMESTAMP,
        )
        self.assertIsNone(result["tcn"])

    def test_null_po_reference(self):
        result = transform_record(
            self._make_record(PO_REFERENCE=None), now=FIXED_TIMESTAMP,
        )
        self.assertIsNone(result["procurement_order_id"])

    def test_empty_po_reference(self):
        result = transform_record(
            self._make_record(PO_REFERENCE=""), now=FIXED_TIMESTAMP,
        )
        self.assertIsNone(result["procurement_order_id"])

    def test_null_material_and_nsn(self):
        result = transform_record(
            self._make_record(MATERIAL_NUM=None, NSN=None), now=FIXED_TIMESTAMP,
        )
        self.assertIsNone(result["item_id"])

    def test_empty_material_falls_back_to_nsn(self):
        result = transform_record(
            self._make_record(MATERIAL_NUM="", NSN="2940-01-576-4108"),
            now=FIXED_TIMESTAMP,
        )
        self.assertIsNotNone(result["item_id"])

    def test_null_quantity(self):
        result = transform_record(
            self._make_record(QUANTITY=None), now=FIXED_TIMESTAMP,
        )
        self.assertIsNone(result["quantity"])

    def test_null_weight(self):
        result = transform_record(
            self._make_record(WEIGHT_LBS=None), now=FIXED_TIMESTAMP,
        )
        self.assertIsNone(result["weight_lbs"])

    def test_missing_shipment_id_raises(self):
        record = self._make_record()
        del record["SHIPMENT_ID"]
        with self.assertRaises(ValidationError):
            transform_record(record, now=FIXED_TIMESTAMP)

    def test_empty_shipment_id_raises(self):
        with self.assertRaises(ValidationError):
            transform_record(
                self._make_record(SHIPMENT_ID=""), now=FIXED_TIMESTAMP,
            )

    def test_whitespace_only_fields_treated_as_null(self):
        result = transform_record(
            self._make_record(CARRIER="   ", TCN="  "), now=FIXED_TIMESTAMP,
        )
        self.assertIsNone(result["carrier"])
        self.assertIsNone(result["tcn"])


class TestStatusMapping(unittest.TestCase):
    """Verify all known status values map correctly."""

    def test_in_transit(self):
        self.assertEqual(map_status("IN_TRANSIT"), "IN_TRANSIT")

    def test_delivered(self):
        self.assertEqual(map_status("DELIVERED"), "DELIVERED")

    def test_pending(self):
        self.assertEqual(map_status("PENDING"), "PENDING")

    def test_returned(self):
        self.assertEqual(map_status("RETURNED"), "RETURNED")

    def test_cancelled_maps_to_returned(self):
        self.assertEqual(map_status("CANCELLED"), "RETURNED")

    def test_shipped_maps_to_in_transit(self):
        self.assertEqual(map_status("SHIPPED"), "IN_TRANSIT")

    def test_unknown_defaults_to_pending(self):
        self.assertEqual(map_status("FOOBAR"), "PENDING")

    def test_empty_defaults_to_pending(self):
        self.assertEqual(map_status(""), "PENDING")

    def test_none_defaults_to_pending(self):
        self.assertEqual(map_status(None), "PENDING")

    def test_case_insensitive(self):
        self.assertEqual(map_status("in_transit"), "IN_TRANSIT")
        self.assertEqual(map_status("Delivered"), "DELIVERED")


class TestShipmentTypeMapping(unittest.TestCase):

    def test_valid_types(self):
        for t in ["SURFACE", "AIR", "SEALIFT", "MULTIMODAL"]:
            self.assertEqual(map_shipment_type(t), t)

    def test_unknown_defaults_to_surface(self):
        self.assertEqual(map_shipment_type("RAIL"), "SURFACE")

    def test_empty_defaults_to_surface(self):
        self.assertEqual(map_shipment_type(""), "SURFACE")

    def test_none_defaults_to_surface(self):
        self.assertEqual(map_shipment_type(None), "SURFACE")


class TestDateParsing(unittest.TestCase):

    def test_iso_date(self):
        self.assertEqual(parse_date("2024-01-10"), "2024-01-10")

    def test_sap_internal_format(self):
        self.assertEqual(parse_date("20240110"), "2024-01-10")

    def test_none(self):
        self.assertIsNone(parse_date(None))

    def test_empty_string(self):
        self.assertIsNone(parse_date(""))

    def test_whitespace(self):
        self.assertIsNone(parse_date("   "))

    def test_invalid_raises(self):
        with self.assertRaises(ValueError):
            parse_date("not-a-date")

    def test_datetime_object(self):
        dt = datetime(2024, 1, 10, 8, 30, 0, tzinfo=timezone.utc)
        self.assertEqual(parse_date(dt), "2024-01-10")


class TestDecimalParsing(unittest.TestCase):

    def test_float_input(self):
        result = parse_decimal(100.0, "QUANTITY")
        self.assertEqual(result, Decimal("100.0"))

    def test_string_input(self):
        result = parse_decimal("245.00", "WEIGHT_LBS")
        self.assertEqual(result, Decimal("245.00"))

    def test_none_input(self):
        self.assertIsNone(parse_decimal(None, "QUANTITY"))

    def test_empty_string(self):
        self.assertIsNone(parse_decimal("", "QUANTITY"))

    def test_already_decimal(self):
        d = Decimal("50.5")
        self.assertIs(parse_decimal(d, "QUANTITY"), d)

    def test_invalid_raises(self):
        with self.assertRaises(ValueError):
            parse_decimal("abc", "QUANTITY")


class TestValidation(unittest.TestCase):

    def test_valid_record_no_issues(self):
        issues = validate_record(SAMPLE_RECORD_1)
        self.assertEqual(issues, [])

    def test_missing_shipment_id(self):
        record = dict(SAMPLE_RECORD_1)
        record["SHIPMENT_ID"] = ""
        issues = validate_record(record)
        self.assertTrue(any("SHIPMENT_ID" in i for i in issues))

    def test_missing_origin_dodaac(self):
        record = dict(SAMPLE_RECORD_1)
        record["ORIGIN_DODAAC"] = ""
        issues = validate_record(record)
        self.assertTrue(any("ORIGIN_DODAAC" in i for i in issues))

    def test_dodaac_too_long(self):
        record = dict(SAMPLE_RECORD_1)
        record["ORIGIN_DODAAC"] = "W45G09X"
        issues = validate_record(record)
        self.assertTrue(any("exceeds 6" in i for i in issues))


class TestRunMigration(unittest.TestCase):
    """Integration test for the full batch migration."""

    def test_both_sample_records(self):
        results, stats = run_migration(
            [SAMPLE_RECORD_1, SAMPLE_RECORD_2], now=FIXED_TIMESTAMP,
        )
        self.assertEqual(stats.total, 2)
        self.assertEqual(stats.transformed, 2)
        self.assertEqual(stats.skipped, 0)
        self.assertEqual(stats.errors, 0)
        self.assertEqual(len(results), 2)

    def test_invalid_record_skipped(self):
        bad_record = {"SHIP_TYPE": "SURFACE"}  # missing SHIPMENT_ID
        results, stats = run_migration(
            [SAMPLE_RECORD_1, bad_record], now=FIXED_TIMESTAMP,
        )
        self.assertEqual(stats.total, 2)
        self.assertEqual(stats.transformed, 1)
        self.assertEqual(stats.skipped, 1)
        self.assertEqual(len(results), 1)

    def test_empty_input(self):
        results, stats = run_migration([], now=FIXED_TIMESTAMP)
        self.assertEqual(stats.total, 0)
        self.assertEqual(stats.transformed, 0)
        self.assertEqual(len(results), 0)

    def test_stats_summary(self):
        _, stats = run_migration(
            [SAMPLE_RECORD_1, SAMPLE_RECORD_2], now=FIXED_TIMESTAMP,
        )
        summary = stats.summary()
        self.assertIn("total_records", summary)
        self.assertIn("transformed", summary)
        self.assertIn("skipped", summary)
        self.assertIn("errors", summary)
        self.assertIn("error_details", summary)

    def test_all_target_fields_present(self):
        """Every record must contain all 22 ALERP shipments fields."""
        expected_fields = {
            "shipment_id", "legacy_system", "legacy_shipment_id", "tcn",
            "shipment_type", "origin_dodaac", "origin_name",
            "destination_dodaac", "destination_name", "item_id",
            "procurement_order_id", "quantity", "weight_lbs", "ship_date",
            "estimated_arrival", "actual_arrival", "carrier", "status",
            "hazmat_class", "created_at", "updated_at",
        }
        results, _ = run_migration(
            [SAMPLE_RECORD_1, SAMPLE_RECORD_2], now=FIXED_TIMESTAMP,
        )
        for rec in results:
            self.assertEqual(set(rec.keys()), expected_fields)


if __name__ == "__main__":
    unittest.main()
