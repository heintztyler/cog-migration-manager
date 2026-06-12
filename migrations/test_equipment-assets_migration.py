"""
Tests for the GCSS-Army EQUI_MASTER -> ALERP assets migration script.
"""

import unittest
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

# Module under test — lives alongside this file in migrations/
from importlib import import_module

migration = import_module("equipment-assets_migration")

transform_record = migration.transform_record
migrate = migration.migrate

# ---------------------------------------------------------------------------
# Sample data matching the three records provided in the migration spec
# ---------------------------------------------------------------------------
SAMPLE_RECORDS = [
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


class TestFieldMappings(unittest.TestCase):
    """Verify each source field maps to the correct target field."""

    def setUp(self):
        self.row = transform_record(SAMPLE_RECORDS[0])

    def test_asset_id_is_valid_uuid(self):
        uuid.UUID(self.row["asset_id"])  # raises on invalid

    def test_legacy_system(self):
        self.assertEqual(self.row["legacy_system"], "GCSS_ARMY")

    def test_legacy_id(self):
        self.assertEqual(self.row["legacy_id"], "000000000010045231")

    def test_nsn(self):
        self.assertEqual(self.row["nsn"], "2350-01-087-1095")

    def test_lin(self):
        self.assertEqual(self.row["lin"], "M77A2B")

    def test_nomenclature(self):
        self.assertEqual(self.row["nomenclature"], "M1A2 ABRAMS MAIN BATTLE TANK")

    def test_short_name_truncated_to_50(self):
        self.assertLessEqual(len(self.row["short_name"]), 50)

    def test_asset_category(self):
        self.assertEqual(self.row["asset_category"], "TRACKED_VEHICLE")

    def test_serial_number(self):
        self.assertEqual(self.row["serial_number"], "GDLS-2019-4521")

    def test_manufacturer(self):
        self.assertEqual(self.row["manufacturer"], "GENERAL DYNAMICS LAND SYSTEMS")

    def test_manufacturer_cage_is_none(self):
        self.assertIsNone(self.row["manufacturer_cage"])

    def test_acquisition_date(self):
        self.assertEqual(self.row["acquisition_date"], "2018-11-20")

    def test_acquisition_cost(self):
        self.assertEqual(Decimal(self.row["acquisition_cost"]), Decimal("6210000.00"))

    def test_fielding_date(self):
        self.assertEqual(self.row["fielding_date"], "2019-03-15")

    def test_owning_uic(self):
        self.assertEqual(self.row["owning_uic"], "W45XAA")

    def test_owning_unit_name(self):
        self.assertEqual(self.row["owning_unit_name"], "2ABCT, 1AD")

    def test_installation(self):
        self.assertEqual(self.row["installation"], "FH01")

    def test_location_detail(self):
        self.assertEqual(self.row["location_detail"], "MTR_POOL_A")

    def test_readiness_status_fmc(self):
        self.assertEqual(self.row["readiness_status"], "FMC")

    def test_status_reason_none_when_fmc(self):
        self.assertIsNone(self.row["status_reason"])

    def test_created_at_is_iso_timestamp(self):
        datetime.fromisoformat(self.row["created_at"])

    def test_updated_at_is_iso_timestamp(self):
        datetime.fromisoformat(self.row["updated_at"])

    def test_updated_by(self):
        self.assertEqual(self.row["updated_by"], "SGT.JOHNSON")


class TestReadinessStatusLogic(unittest.TestCase):
    """status_reason should only be populated for non-FMC assets."""

    def test_pmc_carries_status_reason(self):
        row = transform_record(SAMPLE_RECORDS[1])
        self.assertEqual(row["readiness_status"], "PMC")
        self.assertEqual(row["status_reason"], "PARTIALLY MISSION CAPABLE")

    def test_fmc_has_no_status_reason(self):
        row = transform_record(SAMPLE_RECORDS[0])
        self.assertIsNone(row["status_reason"])


class TestIdempotency(unittest.TestCase):
    """Re-running on the same source must produce identical asset_ids."""

    def test_deterministic_uuid(self):
        row_a = transform_record(SAMPLE_RECORDS[0])
        row_b = transform_record(SAMPLE_RECORDS[0])
        self.assertEqual(row_a["asset_id"], row_b["asset_id"])

    def test_different_records_get_different_ids(self):
        ids = {transform_record(r)["asset_id"] for r in SAMPLE_RECORDS}
        self.assertEqual(len(ids), len(SAMPLE_RECORDS))


class TestTypeCorrectness(unittest.TestCase):
    """Validate Python types of transformed output values."""

    def setUp(self):
        self.row = transform_record(SAMPLE_RECORDS[0])

    def test_asset_id_type(self):
        self.assertIsInstance(self.row["asset_id"], str)
        uuid.UUID(self.row["asset_id"])

    def test_acquisition_cost_decimal_string(self):
        d = Decimal(self.row["acquisition_cost"])
        self.assertEqual(d, d.quantize(Decimal("0.01")))

    def test_dates_are_iso_strings(self):
        for field in ("acquisition_date", "fielding_date"):
            date.fromisoformat(self.row[field])

    def test_timestamps_are_iso_strings(self):
        for field in ("created_at", "updated_at"):
            datetime.fromisoformat(self.row[field])


class TestEdgeCases(unittest.TestCase):
    """Graceful handling of NULL / empty / unexpected values."""

    def _minimal_record(self, **overrides):
        base = {"EQUNR": "000000000099999999", "WAESSION": "USD"}
        base.update(overrides)
        return base

    def test_missing_equnr_raises(self):
        with self.assertRaises(ValueError):
            transform_record({})

    def test_empty_equnr_raises(self):
        with self.assertRaises(ValueError):
            transform_record({"EQUNR": "", "WAESSION": "USD"})

    def test_none_fields_produce_none(self):
        row = transform_record(self._minimal_record())
        self.assertIsNone(row["nsn"])
        self.assertIsNone(row["lin"])
        self.assertIsNone(row["nomenclature"])
        self.assertIsNone(row["short_name"])
        self.assertIsNone(row["serial_number"])
        self.assertIsNone(row["manufacturer"])
        self.assertIsNone(row["acquisition_date"])
        self.assertIsNone(row["acquisition_cost"])
        self.assertIsNone(row["fielding_date"])
        self.assertIsNone(row["owning_uic"])
        self.assertIsNone(row["owning_unit_name"])

    def test_empty_string_fields_produce_none(self):
        row = transform_record(self._minimal_record(
            NSN="", LIN_NUM="", TXTMI="", HERST="",
        ))
        self.assertIsNone(row["nsn"])
        self.assertIsNone(row["lin"])
        self.assertIsNone(row["nomenclature"])
        self.assertIsNone(row["manufacturer"])

    def test_whitespace_only_fields_produce_none(self):
        row = transform_record(self._minimal_record(SERGE="   "))
        self.assertIsNone(row["serial_number"])

    def test_unknown_eqtyp_maps_to_unknown(self):
        row = transform_record(self._minimal_record(EQTYP="Z", EQART="MYSTERY"))
        self.assertEqual(row["asset_category"], "UNKNOWN")

    def test_sap_yyyymmdd_date_format(self):
        row = transform_record(self._minimal_record(ANSDT="20210503"))
        self.assertEqual(row["acquisition_date"], "2021-05-03")

    def test_invalid_date_returns_none(self):
        row = transform_record(self._minimal_record(ANSDT="NOT-A-DATE"))
        self.assertIsNone(row["acquisition_date"])

    def test_invalid_decimal_returns_none(self):
        row = transform_record(self._minimal_record(ANSWT="INVALID"))
        self.assertIsNone(row["acquisition_cost"])

    def test_invalid_readiness_returns_none(self):
        row = transform_record(self._minimal_record(USTATUS="XYZ"))
        self.assertIsNone(row["readiness_status"])


class TestMigrateFunction(unittest.TestCase):
    """Integration tests for the top-level migrate() orchestrator."""

    def test_all_sample_records_succeed(self):
        result = migrate(SAMPLE_RECORDS)
        self.assertEqual(result["stats"]["total_input"], 3)
        self.assertEqual(result["stats"]["succeeded"], 3)
        self.assertEqual(result["stats"]["errors"], 0)
        self.assertEqual(result["stats"]["skipped"], 0)
        self.assertEqual(len(result["transformed"]), 3)

    def test_non_usd_record_skipped(self):
        records = [
            {"EQUNR": "000000000010045231", "WAESSION": "EUR",
             "EQTYP": "V", "EQART": "TRACKED_VH"},
        ]
        result = migrate(records)
        self.assertEqual(result["stats"]["skipped"], 1)
        self.assertEqual(result["stats"]["succeeded"], 0)
        self.assertEqual(len(result["transformed"]), 0)

    def test_bad_record_captured_in_errors(self):
        records = [{"NOT_EQUNR": "missing"}]
        result = migrate(records)
        self.assertEqual(result["stats"]["errors"], 1)
        self.assertEqual(len(result["errors"]), 1)

    def test_empty_input(self):
        result = migrate([])
        self.assertEqual(result["stats"]["total_input"], 0)
        self.assertEqual(result["stats"]["succeeded"], 0)

    def test_mixed_good_and_bad_records(self):
        records = [
            SAMPLE_RECORDS[0],                           # good
            {"EQUNR": "000000000010045232", "WAESSION": "EUR"},  # skipped (non-USD)
            {},                                          # error (no EQUNR)
            SAMPLE_RECORDS[2],                           # good
        ]
        result = migrate(records)
        self.assertEqual(result["stats"]["total_input"], 4)
        self.assertEqual(result["stats"]["succeeded"], 2)
        self.assertEqual(result["stats"]["skipped"], 1)
        self.assertEqual(result["stats"]["errors"], 1)


class TestAllRequiredFieldsPresent(unittest.TestCase):
    """Every key in the target schema must appear in the output dict."""

    REQUIRED_KEYS = {
        "asset_id", "legacy_system", "legacy_id", "nsn", "lin",
        "nomenclature", "short_name", "asset_category", "serial_number",
        "manufacturer", "manufacturer_cage", "acquisition_date",
        "acquisition_cost", "fielding_date", "owning_uic",
        "owning_unit_name", "installation", "location_detail",
        "readiness_status", "status_reason", "created_at", "updated_at",
        "updated_by",
    }

    def test_all_keys_present(self):
        row = transform_record(SAMPLE_RECORDS[0])
        self.assertEqual(set(row.keys()), self.REQUIRED_KEYS)


if __name__ == "__main__":
    unittest.main()
