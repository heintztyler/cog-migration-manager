"""
Legacy System Alpha: GCSS-Army (Global Combat Support System - Army)
Handles equipment/asset tracking, maintenance work orders, and supply requisitions.

This system uses older SAP naming conventions with German-influenced field names,
BAPI-style structures, and SAP table naming (e.g., EQUI, AUFK, MARA).
"""

SYSTEM_NAME = "GCSS-Army"
SYSTEM_DESCRIPTION = (
    "Global Combat Support System - Army. Manages tactical and operational logistics "
    "including equipment readiness, maintenance scheduling, and supply chain operations "
    "for combat and combat support units."
)

# Schema definitions mimicking SAP PM/MM module structures
SCHEMAS = {
    "EQUI_MASTER": {
        "description": "Equipment Master Records - Tracks all Army equipment assets",
        "table_name": "EQUI_MASTER",
        "fields": [
            {"name": "EQUNR", "type": "VARCHAR(18)", "description": "Equipment Number", "example": "000000000010045231"},
            {"name": "EQTYP", "type": "VARCHAR(1)", "description": "Equipment Category", "example": "V"},
            {"name": "TXTMI", "type": "VARCHAR(40)", "description": "Description (Short Text)", "example": "M1A2 ABRAMS MAIN BATTLE TANK"},
            {"name": "EQART", "type": "VARCHAR(10)", "description": "Type of Technical Object", "example": "TRACKED_VH"},
            {"name": "INBDT", "type": "DATE", "description": "Start-up Date", "example": "2019-03-15"},
            {"name": "HERST", "type": "VARCHAR(30)", "description": "Manufacturer", "example": "GENERAL DYNAMICS LAND SYSTEMS"},
            {"name": "SERGE", "type": "VARCHAR(20)", "description": "Serial Number", "example": "GDLS-2019-4521"},
            {"name": "ANSDT", "type": "DATE", "description": "Acquisition Date", "example": "2018-11-20"},
            {"name": "ANSWT", "type": "DECIMAL(13,2)", "description": "Acquisition Value", "example": "6210000.00"},
            {"name": "WAESSION", "type": "VARCHAR(5)", "description": "Currency Key", "example": "USD"},
            {"name": "IWERK", "type": "VARCHAR(4)", "description": "Maintenance Plant", "example": "FH01"},
            {"name": "SWERK", "type": "VARCHAR(4)", "description": "Maintenance Planning Plant", "example": "FH01"},
            {"name": "STORT", "type": "VARCHAR(10)", "description": "Storage Location", "example": "MTR_POOL_A"},
            {"name": "TPLNR", "type": "VARCHAR(30)", "description": "Functional Location", "example": "US-ARMY-III-1AD-2ABCT"},
            {"name": "USTATUS", "type": "VARCHAR(4)", "description": "User Status", "example": "FMC"},
            {"name": "STATTEXT", "type": "VARCHAR(20)", "description": "Status Description", "example": "FULLY MISSION CAPABLE"},
            {"name": "GEWRK", "type": "VARCHAR(12)", "description": "Responsible Work Center", "example": "MAINT_CO_A"},
            {"name": "LIN_NUM", "type": "VARCHAR(10)", "description": "LIN (Line Item Number)", "example": "M77A2B"},
            {"name": "NSN", "type": "VARCHAR(13)", "description": "National Stock Number", "example": "2350-01-087-1095"},
            {"name": "UIC", "type": "VARCHAR(6)", "description": "Unit Identification Code", "example": "W45XAA"},
            {"name": "AEDAT", "type": "DATE", "description": "Last Changed On", "example": "2024-01-15"},
            {"name": "AENAM", "type": "VARCHAR(12)", "description": "Last Changed By", "example": "SGT.JOHNSON"},
        ],
    },
    "AUFK_WORKORDER": {
        "description": "Maintenance Work Orders - Tracks all maintenance activities",
        "table_name": "AUFK_WORKORDER",
        "fields": [
            {"name": "AUFNR", "type": "VARCHAR(12)", "description": "Order Number", "example": "000004521001"},
            {"name": "AUTYP", "type": "VARCHAR(2)", "description": "Order Type", "example": "PM"},
            {"name": "AUART", "type": "VARCHAR(4)", "description": "Order Category", "example": "PM01"},
            {"name": "KTEXT", "type": "VARCHAR(40)", "description": "Short Text", "example": "SCHEDULED MAINT - ENGINE OVERHAUL"},
            {"name": "EQUNR", "type": "VARCHAR(18)", "description": "Equipment Number", "example": "000000000010045231"},
            {"name": "TPLNR", "type": "VARCHAR(30)", "description": "Functional Location", "example": "US-ARMY-III-1AD-2ABCT"},
            {"name": "PRIESSION", "type": "VARCHAR(1)", "description": "Priority", "example": "2"},
            {"name": "GSTRP", "type": "DATE", "description": "Scheduled Start Date", "example": "2024-02-01"},
            {"name": "GLTRP", "type": "DATE", "description": "Scheduled Finish Date", "example": "2024-02-15"},
            {"name": "ERDAT", "type": "DATE", "description": "Created On", "example": "2024-01-20"},
            {"name": "ERNAM", "type": "VARCHAR(12)", "description": "Created By", "example": "CW3.MARTINEZ"},
            {"name": "ARBPL", "type": "VARCHAR(8)", "description": "Work Center", "example": "MAINT_3A"},
            {"name": "IPHAS", "type": "VARCHAR(4)", "description": "Maintenance Phase", "example": "EXEC"},
            {"name": "KOSTL", "type": "VARCHAR(10)", "description": "Cost Center", "example": "CC-1AD-MNT"},
            {"name": "OVERALL_STAT", "type": "VARCHAR(4)", "description": "System Status", "example": "REL"},
            {"name": "MAN_HOURS", "type": "DECIMAL(7,2)", "description": "Planned Man-Hours", "example": "240.00"},
            {"name": "ACT_HOURS", "type": "DECIMAL(7,2)", "description": "Actual Man-Hours", "example": "186.50"},
            {"name": "FAULT_CODE", "type": "VARCHAR(8)", "description": "Fault/Damage Code", "example": "ENG-0042"},
        ],
    },
    "MARA_SUPPLY": {
        "description": "Supply/Material Master - Tracks spare parts and consumables",
        "table_name": "MARA_SUPPLY",
        "fields": [
            {"name": "MATNR", "type": "VARCHAR(18)", "description": "Material Number", "example": "000000000050012345"},
            {"name": "MAKTX", "type": "VARCHAR(40)", "description": "Material Description", "example": "FILTER, OIL, ENGINE - M1A2"},
            {"name": "MTART", "type": "VARCHAR(4)", "description": "Material Type", "example": "ERSA"},
            {"name": "MATKL", "type": "VARCHAR(9)", "description": "Material Group", "example": "ENG_PARTS"},
            {"name": "NSN", "type": "VARCHAR(13)", "description": "National Stock Number", "example": "2940-01-576-4108"},
            {"name": "MEINS", "type": "VARCHAR(3)", "description": "Base Unit of Measure", "example": "EA"},
            {"name": "BRGEW", "type": "DECIMAL(13,3)", "description": "Gross Weight", "example": "2.450"},
            {"name": "GEWEI", "type": "VARCHAR(3)", "description": "Weight Unit", "example": "LB"},
            {"name": "LABST", "type": "INTEGER", "description": "Qty On Hand", "example": "142"},
            {"name": "MINBE", "type": "INTEGER", "description": "Reorder Point", "example": "50"},
            {"name": "EISBE", "type": "INTEGER", "description": "Safety Stock", "example": "25"},
            {"name": "LGORT", "type": "VARCHAR(4)", "description": "Storage Location", "example": "WH01"},
            {"name": "LIFNR", "type": "VARCHAR(10)", "description": "Vendor Number", "example": "0000005432"},
            {"name": "EKGRP", "type": "VARCHAR(3)", "description": "Purchasing Group", "example": "P01"},
            {"name": "PRICE", "type": "DECIMAL(11,2)", "description": "Standard Price", "example": "47.50"},
            {"name": "WAESSION", "type": "VARCHAR(5)", "description": "Currency", "example": "USD"},
            {"name": "SHELF_LIFE", "type": "INTEGER", "description": "Shelf Life (Days)", "example": "730"},
            {"name": "HAZMAT_IND", "type": "VARCHAR(1)", "description": "Hazmat Indicator", "example": "N"},
            {"name": "LAST_RECEIPT", "type": "DATE", "description": "Last Goods Receipt Date", "example": "2024-01-10"},
        ],
    },
    "UNIT_READINESS": {
        "description": "Unit Readiness Reports - Daily equipment status rollup by unit",
        "table_name": "UNIT_READINESS",
        "fields": [
            {"name": "REPORT_ID", "type": "VARCHAR(20)", "description": "Report Identifier", "example": "USR-2024-0115-1AD"},
            {"name": "UIC", "type": "VARCHAR(6)", "description": "Unit Identification Code", "example": "W45XAA"},
            {"name": "UNIT_NAME", "type": "VARCHAR(50)", "description": "Unit Designation", "example": "2D ABCT, 1ST ARMORED DIV"},
            {"name": "REPORT_DATE", "type": "DATE", "description": "Report Date", "example": "2024-01-15"},
            {"name": "EQUIP_CAT", "type": "VARCHAR(10)", "description": "Equipment Category", "example": "TRACKED_VH"},
            {"name": "AUTH_QTY", "type": "INTEGER", "description": "Authorized Quantity", "example": "58"},
            {"name": "ON_HAND", "type": "INTEGER", "description": "On-Hand Quantity", "example": "56"},
            {"name": "FMC_QTY", "type": "INTEGER", "description": "Fully Mission Capable Qty", "example": "48"},
            {"name": "PMC_QTY", "type": "INTEGER", "description": "Partially Mission Capable Qty", "example": "5"},
            {"name": "NMC_QTY", "type": "INTEGER", "description": "Not Mission Capable Qty", "example": "3"},
            {"name": "FMC_RATE", "type": "DECIMAL(5,2)", "description": "FMC Rate (%)", "example": "85.71"},
            {"name": "DEADLINE_QTY", "type": "INTEGER", "description": "Deadline (Awaiting Parts)", "example": "2"},
            {"name": "REMARKS", "type": "VARCHAR(200)", "description": "Commander Remarks", "example": "2x M1A2 AWAITING POWERPACK; ESD 30JAN"},
        ],
    },
}

# Sample data for each table
SAMPLE_DATA = {
    "EQUI_MASTER": [
        {"EQUNR": "000000000010045231", "EQTYP": "V", "TXTMI": "M1A2 ABRAMS MAIN BATTLE TANK", "EQART": "TRACKED_VH", "INBDT": "2019-03-15", "HERST": "GENERAL DYNAMICS LAND SYSTEMS", "SERGE": "GDLS-2019-4521", "ANSDT": "2018-11-20", "ANSWT": 6210000.00, "WAESSION": "USD", "IWERK": "FH01", "SWERK": "FH01", "STORT": "MTR_POOL_A", "TPLNR": "US-ARMY-III-1AD-2ABCT", "USTATUS": "FMC", "STATTEXT": "FULLY MISSION CAPABLE", "GEWRK": "MAINT_CO_A", "LIN_NUM": "M77A2B", "NSN": "2350-01-087-1095", "UIC": "W45XAA", "AEDAT": "2024-01-15", "AENAM": "SGT.JOHNSON"},
        {"EQUNR": "000000000010045232", "EQTYP": "V", "TXTMI": "M2A3 BRADLEY FIGHTING VEHICLE", "EQART": "TRACKED_VH", "INBDT": "2020-06-22", "HERST": "BAE SYSTEMS", "SERGE": "BAE-2020-7821", "ANSDT": "2020-01-15", "ANSWT": 3200000.00, "WAESSION": "USD", "IWERK": "FH01", "SWERK": "FH01", "STORT": "MTR_POOL_B", "TPLNR": "US-ARMY-III-1AD-2ABCT", "USTATUS": "PMC", "STATTEXT": "PARTIALLY MISSION CAPABLE", "GEWRK": "MAINT_CO_A", "LIN_NUM": "M62A3D", "NSN": "2350-01-579-2501", "UIC": "W45XAA", "AEDAT": "2024-01-14", "AENAM": "SPC.WILLIAMS"},
        {"EQUNR": "000000000010045240", "EQTYP": "V", "TXTMI": "M109A7 PALADIN HOWITZER", "EQART": "TRACKED_VH", "INBDT": "2021-09-10", "HERST": "BAE SYSTEMS", "SERGE": "BAE-2021-1102", "ANSDT": "2021-05-03", "ANSWT": 4800000.00, "WAESSION": "USD", "IWERK": "FH01", "SWERK": "FH01", "STORT": "MTR_POOL_C", "TPLNR": "US-ARMY-III-1AD-DIVARTY", "USTATUS": "FMC", "STATTEXT": "FULLY MISSION CAPABLE", "GEWRK": "MAINT_CO_B", "LIN_NUM": "M90A7E", "NSN": "2350-01-614-4321", "UIC": "W45XBB", "AEDAT": "2024-01-12", "AENAM": "SSG.CHEN"},
        {"EQUNR": "000000000010045250", "EQTYP": "V", "TXTMI": "HMMWV M1151 UP-ARMORED", "EQART": "WHEELED_VH", "INBDT": "2017-04-01", "HERST": "AM GENERAL", "SERGE": "AMG-2017-9934", "ANSDT": "2016-12-15", "ANSWT": 220000.00, "WAESSION": "USD", "IWERK": "FH01", "SWERK": "FH01", "STORT": "MTR_POOL_A", "TPLNR": "US-ARMY-III-1AD-2ABCT", "USTATUS": "NMC", "STATTEXT": "NOT MISSION CAPABLE", "GEWRK": "MAINT_CO_A", "LIN_NUM": "L55H2A", "NSN": "2320-01-541-4912", "UIC": "W45XAA", "AEDAT": "2024-01-15", "AENAM": "PFC.DAVIS"},
        {"EQUNR": "000000000010045260", "EQTYP": "C", "TXTMI": "AN/TPQ-36 FIREFINDER RADAR", "EQART": "COMM_ELEC", "INBDT": "2018-08-20", "HERST": "THALES RAYTHEON", "SERGE": "TR-2018-3321", "ANSDT": "2018-03-10", "ANSWT": 15400000.00, "WAESSION": "USD", "IWERK": "FH01", "SWERK": "FH01", "STORT": "SENS_BAY_1", "TPLNR": "US-ARMY-III-1AD-FIRES", "USTATUS": "FMC", "STATTEXT": "FULLY MISSION CAPABLE", "GEWRK": "MAINT_CO_C", "LIN_NUM": "R21T6F", "NSN": "5985-01-456-7890", "UIC": "W45XCC", "AEDAT": "2024-01-10", "AENAM": "CW2.PARK"},
    ],
    "AUFK_WORKORDER": [
        {"AUFNR": "000004521001", "AUTYP": "PM", "AUART": "PM01", "KTEXT": "SCHEDULED MAINT - ENGINE OVERHAUL", "EQUNR": "000000000010045231", "TPLNR": "US-ARMY-III-1AD-2ABCT", "PRIESSION": "2", "GSTRP": "2024-02-01", "GLTRP": "2024-02-15", "ERDAT": "2024-01-20", "ERNAM": "CW3.MARTINEZ", "ARBPL": "MAINT_3A", "IPHAS": "EXEC", "KOSTL": "CC-1AD-MNT", "OVERALL_STAT": "REL", "MAN_HOURS": 240.00, "ACT_HOURS": 186.50, "FAULT_CODE": "ENG-0042"},
        {"AUFNR": "000004521002", "AUTYP": "PM", "AUART": "PM02", "KTEXT": "UNSCHEDULED - TRANSMISSION FAULT", "EQUNR": "000000000010045250", "TPLNR": "US-ARMY-III-1AD-2ABCT", "PRIESSION": "1", "GSTRP": "2024-01-16", "GLTRP": "2024-01-25", "ERDAT": "2024-01-15", "ERNAM": "SFC.THOMPSON", "ARBPL": "MAINT_2B", "IPHAS": "WAIT", "KOSTL": "CC-1AD-MNT", "OVERALL_STAT": "REL", "MAN_HOURS": 80.00, "ACT_HOURS": 0.00, "FAULT_CODE": "TRN-0018"},
        {"AUFNR": "000004521003", "AUTYP": "PM", "AUART": "PM03", "KTEXT": "ANNUAL SERVICE - TURRET SYSTEMS", "EQUNR": "000000000010045232", "TPLNR": "US-ARMY-III-1AD-2ABCT", "PRIESSION": "3", "GSTRP": "2024-03-01", "GLTRP": "2024-03-05", "ERDAT": "2024-01-22", "ERNAM": "CW3.MARTINEZ", "ARBPL": "MAINT_3A", "IPHAS": "PLAN", "KOSTL": "CC-1AD-MNT", "OVERALL_STAT": "CRTD", "MAN_HOURS": 40.00, "ACT_HOURS": 0.00, "FAULT_CODE": ""},
    ],
    "MARA_SUPPLY": [
        {"MATNR": "000000000050012345", "MAKTX": "FILTER, OIL, ENGINE - M1A2", "MTART": "ERSA", "MATKL": "ENG_PARTS", "NSN": "2940-01-576-4108", "MEINS": "EA", "BRGEW": 2.450, "GEWEI": "LB", "LABST": 142, "MINBE": 50, "EISBE": 25, "LGORT": "WH01", "LIFNR": "0000005432", "EKGRP": "P01", "PRICE": 47.50, "WAESSION": "USD", "SHELF_LIFE": 730, "HAZMAT_IND": "N", "LAST_RECEIPT": "2024-01-10"},
        {"MATNR": "000000000050012400", "MAKTX": "TRACK SHOE, SINGLE PIN - T-158", "MTART": "ERSA", "MATKL": "TRAC_PART", "NSN": "2530-01-595-4455", "MEINS": "EA", "BRGEW": 72.000, "GEWEI": "LB", "LABST": 320, "MINBE": 100, "EISBE": 50, "LGORT": "WH02", "LIFNR": "0000005480", "EKGRP": "P01", "PRICE": 890.00, "WAESSION": "USD", "SHELF_LIFE": 9999, "HAZMAT_IND": "N", "LAST_RECEIPT": "2023-12-20"},
        {"MATNR": "000000000050012500", "MAKTX": "COOLANT, ENGINE ANTIFREEZE", "MTART": "HIBE", "MATKL": "FLUIDS", "NSN": "6850-01-497-2222", "MEINS": "GL", "BRGEW": 8.600, "GEWEI": "LB", "LABST": 85, "MINBE": 30, "EISBE": 15, "LGORT": "WH01", "LIFNR": "0000005500", "EKGRP": "P02", "PRICE": 22.00, "WAESSION": "USD", "SHELF_LIFE": 365, "HAZMAT_IND": "Y", "LAST_RECEIPT": "2024-01-05"},
    ],
    "UNIT_READINESS": [
        {"REPORT_ID": "USR-2024-0115-1AD", "UIC": "W45XAA", "UNIT_NAME": "2D ABCT, 1ST ARMORED DIV", "REPORT_DATE": "2024-01-15", "EQUIP_CAT": "TRACKED_VH", "AUTH_QTY": 58, "ON_HAND": 56, "FMC_QTY": 48, "PMC_QTY": 5, "NMC_QTY": 3, "FMC_RATE": 85.71, "DEADLINE_QTY": 2, "REMARKS": "2x M1A2 AWAITING POWERPACK; ESD 30JAN"},
        {"REPORT_ID": "USR-2024-0115-1AD", "UIC": "W45XAA", "UNIT_NAME": "2D ABCT, 1ST ARMORED DIV", "REPORT_DATE": "2024-01-15", "EQUIP_CAT": "WHEELED_VH", "AUTH_QTY": 245, "ON_HAND": 240, "FMC_QTY": 218, "PMC_QTY": 12, "NMC_QTY": 10, "FMC_RATE": 90.83, "DEADLINE_QTY": 4, "REMARKS": "4x HMMWV AT DEPOT; 3x NMC TRANS FAULT"},
        {"REPORT_ID": "USR-2024-0115-DIV", "UIC": "W45XBB", "UNIT_NAME": "DIVARTY, 1ST ARMORED DIV", "REPORT_DATE": "2024-01-15", "EQUIP_CAT": "TRACKED_VH", "AUTH_QTY": 24, "ON_HAND": 24, "FMC_QTY": 22, "PMC_QTY": 1, "NMC_QTY": 1, "FMC_RATE": 91.67, "DEADLINE_QTY": 0, "REMARKS": "1x M109A7 NMC FIRE CONTROL; PARTS ON ORDER"},
    ],
}
