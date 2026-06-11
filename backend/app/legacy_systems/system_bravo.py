"""
Legacy System Bravo: LMP (Logistics Modernization Program)
Handles procurement/contracts, warehouse management, shipping/transportation,
and financial accounting for logistics operations.

This system uses a different SAP configuration with ECC-style naming,
different field conventions, and a separate organizational structure.
"""

SYSTEM_NAME = "LMP"
SYSTEM_DESCRIPTION = (
    "Logistics Modernization Program. Manages national-level logistics including "
    "procurement, warehousing, distribution, and financial management for Army "
    "materiel command and sustainment operations."
)

SCHEMAS = {
    "VENDOR_MASTER": {
        "description": "Vendor/Supplier Master Data - All contracted suppliers and manufacturers",
        "table_name": "VENDOR_MASTER",
        "fields": [
            {"name": "VENDOR_ID", "type": "VARCHAR(10)", "description": "Vendor Account Number", "example": "V-000054321"},
            {"name": "VENDOR_NAME", "type": "VARCHAR(80)", "description": "Vendor Full Name", "example": "GENERAL DYNAMICS LAND SYSTEMS LLC"},
            {"name": "VENDOR_NAME2", "type": "VARCHAR(80)", "description": "Vendor Name Line 2", "example": "COMBAT SYSTEMS DIVISION"},
            {"name": "STREET", "type": "VARCHAR(60)", "description": "Street Address", "example": "38500 MOUND RD"},
            {"name": "CITY", "type": "VARCHAR(40)", "description": "City", "example": "STERLING HEIGHTS"},
            {"name": "STATE_CODE", "type": "VARCHAR(2)", "description": "State/Region", "example": "MI"},
            {"name": "POSTAL_CODE", "type": "VARCHAR(10)", "description": "ZIP/Postal Code", "example": "48310"},
            {"name": "COUNTRY", "type": "VARCHAR(3)", "description": "Country Code", "example": "US"},
            {"name": "CAGE_CODE", "type": "VARCHAR(5)", "description": "CAGE Code (Commercial And Government Entity)", "example": "1GDL5"},
            {"name": "DUNS_NUMBER", "type": "VARCHAR(13)", "description": "DUNS Number", "example": "0068244950000"},
            {"name": "TAX_ID", "type": "VARCHAR(16)", "description": "Tax Identification Number", "example": "38-XXXXXXX"},
            {"name": "PURCH_ORG", "type": "VARCHAR(4)", "description": "Purchasing Organization", "example": "AMC1"},
            {"name": "PAYMENT_TERMS", "type": "VARCHAR(4)", "description": "Payment Terms Key", "example": "NT30"},
            {"name": "VENDOR_CLASS", "type": "VARCHAR(10)", "description": "Vendor Classification", "example": "PRIME_DEF"},
            {"name": "SMALL_BIZ_IND", "type": "VARCHAR(1)", "description": "Small Business Indicator", "example": "N"},
            {"name": "ACTIVE_FLAG", "type": "VARCHAR(1)", "description": "Active Status", "example": "Y"},
            {"name": "CREATED_DATE", "type": "DATE", "description": "Record Created Date", "example": "2015-06-20"},
            {"name": "LAST_PO_DATE", "type": "DATE", "description": "Date of Last PO", "example": "2024-01-08"},
        ],
    },
    "PURCHASE_ORDERS": {
        "description": "Purchase Order Headers - All procurement transactions",
        "table_name": "PURCHASE_ORDERS",
        "fields": [
            {"name": "PO_NUMBER", "type": "VARCHAR(10)", "description": "Purchase Order Number", "example": "4500089231"},
            {"name": "PO_TYPE", "type": "VARCHAR(4)", "description": "PO Document Type", "example": "STPO"},
            {"name": "VENDOR_ID", "type": "VARCHAR(10)", "description": "Vendor Account", "example": "V-000054321"},
            {"name": "PO_DATE", "type": "DATE", "description": "PO Creation Date", "example": "2024-01-08"},
            {"name": "PURCH_ORG", "type": "VARCHAR(4)", "description": "Purchasing Organization", "example": "AMC1"},
            {"name": "PURCH_GROUP", "type": "VARCHAR(3)", "description": "Purchasing Group", "example": "PG1"},
            {"name": "COMP_CODE", "type": "VARCHAR(4)", "description": "Company Code", "example": "D100"},
            {"name": "CONTRACT_REF", "type": "VARCHAR(20)", "description": "Contract Reference", "example": "W56HZV-20-C-0045"},
            {"name": "TOTAL_VALUE", "type": "DECIMAL(15,2)", "description": "Total PO Value", "example": "1245000.00"},
            {"name": "CURRENCY", "type": "VARCHAR(3)", "description": "Currency Code", "example": "USD"},
            {"name": "DELIVERY_DATE", "type": "DATE", "description": "Requested Delivery Date", "example": "2024-04-15"},
            {"name": "SHIP_TO_DODAAC", "type": "VARCHAR(6)", "description": "Ship-To DoDAAC", "example": "W45G09"},
            {"name": "PO_STATUS", "type": "VARCHAR(10)", "description": "PO Status", "example": "APPROVED"},
            {"name": "APPROVAL_DATE", "type": "DATE", "description": "Approval Date", "example": "2024-01-10"},
            {"name": "APPROVED_BY", "type": "VARCHAR(30)", "description": "Approving Official", "example": "COL.RICHARDSON"},
            {"name": "PRIORITY_CODE", "type": "VARCHAR(2)", "description": "Supply Priority", "example": "02"},
            {"name": "FUND_CODE", "type": "VARCHAR(10)", "description": "Fund Cite", "example": "2142A000"},
        ],
    },
    "PO_LINE_ITEMS": {
        "description": "Purchase Order Line Items - Individual items within POs",
        "table_name": "PO_LINE_ITEMS",
        "fields": [
            {"name": "PO_NUMBER", "type": "VARCHAR(10)", "description": "Purchase Order Number", "example": "4500089231"},
            {"name": "LINE_NUM", "type": "INTEGER", "description": "Line Item Number", "example": "10"},
            {"name": "MATERIAL_NUM", "type": "VARCHAR(18)", "description": "Material Number", "example": "000000000050012345"},
            {"name": "DESCRIPTION", "type": "VARCHAR(60)", "description": "Item Description", "example": "FILTER ASSY, OIL, ENGINE M1A2 SEP V3"},
            {"name": "NSN", "type": "VARCHAR(13)", "description": "National Stock Number", "example": "2940-01-576-4108"},
            {"name": "QUANTITY", "type": "DECIMAL(13,3)", "description": "Order Quantity", "example": "500.000"},
            {"name": "UOM", "type": "VARCHAR(3)", "description": "Unit of Measure", "example": "EA"},
            {"name": "UNIT_PRICE", "type": "DECIMAL(11,2)", "description": "Unit Price", "example": "47.50"},
            {"name": "NET_VALUE", "type": "DECIMAL(15,2)", "description": "Net Line Value", "example": "23750.00"},
            {"name": "DELIVERY_DATE", "type": "DATE", "description": "Item Delivery Date", "example": "2024-04-15"},
            {"name": "GR_QTY", "type": "DECIMAL(13,3)", "description": "Goods Received Quantity", "example": "0.000"},
            {"name": "GR_DATE", "type": "DATE", "description": "Last Goods Receipt Date", "example": None},
            {"name": "PLANT", "type": "VARCHAR(4)", "description": "Receiving Plant", "example": "D100"},
            {"name": "STORAGE_LOC", "type": "VARCHAR(4)", "description": "Storage Location", "example": "WH01"},
            {"name": "ITEM_STATUS", "type": "VARCHAR(10)", "description": "Line Item Status", "example": "OPEN"},
        ],
    },
    "WAREHOUSE_INVENTORY": {
        "description": "Warehouse Inventory Positions - Stock levels at depot/warehouse locations",
        "table_name": "WAREHOUSE_INVENTORY",
        "fields": [
            {"name": "WAREHOUSE_ID", "type": "VARCHAR(6)", "description": "Warehouse/Depot DoDAAC", "example": "W45G09"},
            {"name": "WAREHOUSE_NAME", "type": "VARCHAR(60)", "description": "Warehouse Description", "example": "ANNISTON ARMY DEPOT - BLDG 401"},
            {"name": "MATERIAL_NUM", "type": "VARCHAR(18)", "description": "Material Number", "example": "000000000050012345"},
            {"name": "NSN", "type": "VARCHAR(13)", "description": "National Stock Number", "example": "2940-01-576-4108"},
            {"name": "DESCRIPTION", "type": "VARCHAR(60)", "description": "Material Description", "example": "FILTER ASSY, OIL, ENGINE M1A2 SEP V3"},
            {"name": "STOCK_TYPE", "type": "VARCHAR(4)", "description": "Stock Type", "example": "UNRS"},
            {"name": "QTY_ON_HAND", "type": "DECIMAL(13,3)", "description": "Quantity On Hand", "example": "2450.000"},
            {"name": "QTY_RESERVED", "type": "DECIMAL(13,3)", "description": "Quantity Reserved", "example": "500.000"},
            {"name": "QTY_AVAILABLE", "type": "DECIMAL(13,3)", "description": "Available Quantity", "example": "1950.000"},
            {"name": "UOM", "type": "VARCHAR(3)", "description": "Unit of Measure", "example": "EA"},
            {"name": "BIN_LOCATION", "type": "VARCHAR(10)", "description": "Bin/Shelf Location", "example": "A-04-B-12"},
            {"name": "LOT_NUMBER", "type": "VARCHAR(20)", "description": "Lot/Batch Number", "example": "LOT-2023-11-4108"},
            {"name": "EXPIRY_DATE", "type": "DATE", "description": "Expiration Date", "example": "2025-11-30"},
            {"name": "CONDITION_CODE", "type": "VARCHAR(2)", "description": "Condition Code", "example": "A"},
            {"name": "LAST_COUNT_DATE", "type": "DATE", "description": "Last Physical Count Date", "example": "2023-12-15"},
            {"name": "LAST_ISSUE_DATE", "type": "DATE", "description": "Last Issue Date", "example": "2024-01-12"},
            {"name": "UNIT_COST", "type": "DECIMAL(11,2)", "description": "Unit Cost", "example": "47.50"},
            {"name": "TOTAL_VALUE", "type": "DECIMAL(15,2)", "description": "Total Inventory Value", "example": "116375.00"},
        ],
    },
    "SHIPMENT_TRACKING": {
        "description": "Shipment/Transportation Records - Tracks materiel movements between locations",
        "table_name": "SHIPMENT_TRACKING",
        "fields": [
            {"name": "SHIPMENT_ID", "type": "VARCHAR(12)", "description": "Shipment Document Number", "example": "SHP-00891234"},
            {"name": "SHIP_TYPE", "type": "VARCHAR(10)", "description": "Shipment Type", "example": "SURFACE"},
            {"name": "TCN", "type": "VARCHAR(17)", "description": "Transportation Control Number", "example": "W45G09-4108-0001"},
            {"name": "ORIGIN_DODAAC", "type": "VARCHAR(6)", "description": "Origin DoDAAC", "example": "W45G09"},
            {"name": "ORIGIN_NAME", "type": "VARCHAR(60)", "description": "Origin Location Name", "example": "ANNISTON ARMY DEPOT"},
            {"name": "DEST_DODAAC", "type": "VARCHAR(6)", "description": "Destination DoDAAC", "example": "W45XAA"},
            {"name": "DEST_NAME", "type": "VARCHAR(60)", "description": "Destination Location Name", "example": "2ABCT, 1AD - FORT BLISS"},
            {"name": "MATERIAL_NUM", "type": "VARCHAR(18)", "description": "Material Number", "example": "000000000050012345"},
            {"name": "NSN", "type": "VARCHAR(13)", "description": "National Stock Number", "example": "2940-01-576-4108"},
            {"name": "QUANTITY", "type": "DECIMAL(13,3)", "description": "Shipped Quantity", "example": "100.000"},
            {"name": "WEIGHT_LBS", "type": "DECIMAL(11,2)", "description": "Total Weight (lbs)", "example": "245.00"},
            {"name": "SHIP_DATE", "type": "DATE", "description": "Ship Date", "example": "2024-01-10"},
            {"name": "ETA_DATE", "type": "DATE", "description": "Estimated Arrival", "example": "2024-01-17"},
            {"name": "ACTUAL_ARRIVAL", "type": "DATE", "description": "Actual Arrival Date", "example": None},
            {"name": "CARRIER", "type": "VARCHAR(30)", "description": "Carrier/Mode", "example": "DLA DISTRIBUTION"},
            {"name": "TRACKING_STATUS", "type": "VARCHAR(15)", "description": "Current Status", "example": "IN_TRANSIT"},
            {"name": "PO_REFERENCE", "type": "VARCHAR(10)", "description": "Related PO Number", "example": "4500089231"},
            {"name": "HAZMAT_CLASS", "type": "VARCHAR(4)", "description": "Hazmat Classification", "example": "NONE"},
        ],
    },
}

SAMPLE_DATA = {
    "VENDOR_MASTER": [
        {"VENDOR_ID": "V-000054321", "VENDOR_NAME": "GENERAL DYNAMICS LAND SYSTEMS LLC", "VENDOR_NAME2": "COMBAT SYSTEMS DIVISION", "STREET": "38500 MOUND RD", "CITY": "STERLING HEIGHTS", "STATE_CODE": "MI", "POSTAL_CODE": "48310", "COUNTRY": "US", "CAGE_CODE": "1GDL5", "DUNS_NUMBER": "0068244950000", "TAX_ID": "38-XXXXXXX", "PURCH_ORG": "AMC1", "PAYMENT_TERMS": "NT30", "VENDOR_CLASS": "PRIME_DEF", "SMALL_BIZ_IND": "N", "ACTIVE_FLAG": "Y", "CREATED_DATE": "2015-06-20", "LAST_PO_DATE": "2024-01-08"},
        {"VENDOR_ID": "V-000054800", "VENDOR_NAME": "BAE SYSTEMS LAND & ARMAMENTS", "VENDOR_NAME2": "COMBAT VEHICLES", "STREET": "1101 WASHINGTON BLVD", "CITY": "MINNEAPOLIS", "STATE_CODE": "MN", "POSTAL_CODE": "55450", "COUNTRY": "US", "CAGE_CODE": "2BAE8", "DUNS_NUMBER": "0078551230000", "TAX_ID": "41-XXXXXXX", "PURCH_ORG": "AMC1", "PAYMENT_TERMS": "NT30", "VENDOR_CLASS": "PRIME_DEF", "SMALL_BIZ_IND": "N", "ACTIVE_FLAG": "Y", "CREATED_DATE": "2014-03-15", "LAST_PO_DATE": "2024-01-05"},
        {"VENDOR_ID": "V-000055000", "VENDOR_NAME": "HONEYWELL AEROSPACE", "VENDOR_NAME2": "DEFENSE & SPACE", "STREET": "1944 E SKY HARBOR CIR", "CITY": "PHOENIX", "STATE_CODE": "AZ", "POSTAL_CODE": "85034", "COUNTRY": "US", "CAGE_CODE": "3HWL1", "DUNS_NUMBER": "0012345670000", "TAX_ID": "22-XXXXXXX", "PURCH_ORG": "AMC1", "PAYMENT_TERMS": "NT45", "VENDOR_CLASS": "TIER1_SUB", "SMALL_BIZ_IND": "N", "ACTIVE_FLAG": "Y", "CREATED_DATE": "2016-09-10", "LAST_PO_DATE": "2023-12-18"},
    ],
    "PURCHASE_ORDERS": [
        {"PO_NUMBER": "4500089231", "PO_TYPE": "STPO", "VENDOR_ID": "V-000054321", "PO_DATE": "2024-01-08", "PURCH_ORG": "AMC1", "PURCH_GROUP": "PG1", "COMP_CODE": "D100", "CONTRACT_REF": "W56HZV-20-C-0045", "TOTAL_VALUE": 1245000.00, "CURRENCY": "USD", "DELIVERY_DATE": "2024-04-15", "SHIP_TO_DODAAC": "W45G09", "PO_STATUS": "APPROVED", "APPROVAL_DATE": "2024-01-10", "APPROVED_BY": "COL.RICHARDSON", "PRIORITY_CODE": "02", "FUND_CODE": "2142A000"},
        {"PO_NUMBER": "4500089250", "PO_TYPE": "STPO", "VENDOR_ID": "V-000054800", "PO_DATE": "2024-01-05", "PURCH_ORG": "AMC1", "PURCH_GROUP": "PG1", "COMP_CODE": "D100", "CONTRACT_REF": "W56HZV-21-C-0102", "TOTAL_VALUE": 4500000.00, "CURRENCY": "USD", "DELIVERY_DATE": "2024-06-01", "SHIP_TO_DODAAC": "W45G09", "PO_STATUS": "APPROVED", "APPROVAL_DATE": "2024-01-07", "APPROVED_BY": "COL.RICHARDSON", "PRIORITY_CODE": "03", "FUND_CODE": "2142A000"},
    ],
    "PO_LINE_ITEMS": [
        {"PO_NUMBER": "4500089231", "LINE_NUM": 10, "MATERIAL_NUM": "000000000050012345", "DESCRIPTION": "FILTER ASSY, OIL, ENGINE M1A2 SEP V3", "NSN": "2940-01-576-4108", "QUANTITY": 500.000, "UOM": "EA", "UNIT_PRICE": 47.50, "NET_VALUE": 23750.00, "DELIVERY_DATE": "2024-04-15", "GR_QTY": 0.000, "GR_DATE": None, "PLANT": "D100", "STORAGE_LOC": "WH01", "ITEM_STATUS": "OPEN"},
        {"PO_NUMBER": "4500089231", "LINE_NUM": 20, "MATERIAL_NUM": "000000000050012400", "DESCRIPTION": "TRACK SHOE, SINGLE PIN T-158LL", "NSN": "2530-01-595-4455", "QUANTITY": 200.000, "UOM": "EA", "UNIT_PRICE": 890.00, "NET_VALUE": 178000.00, "DELIVERY_DATE": "2024-04-15", "GR_QTY": 0.000, "GR_DATE": None, "PLANT": "D100", "STORAGE_LOC": "WH02", "ITEM_STATUS": "OPEN"},
    ],
    "WAREHOUSE_INVENTORY": [
        {"WAREHOUSE_ID": "W45G09", "WAREHOUSE_NAME": "ANNISTON ARMY DEPOT - BLDG 401", "MATERIAL_NUM": "000000000050012345", "NSN": "2940-01-576-4108", "DESCRIPTION": "FILTER ASSY, OIL, ENGINE M1A2 SEP V3", "STOCK_TYPE": "UNRS", "QTY_ON_HAND": 2450.000, "QTY_RESERVED": 500.000, "QTY_AVAILABLE": 1950.000, "UOM": "EA", "BIN_LOCATION": "A-04-B-12", "LOT_NUMBER": "LOT-2023-11-4108", "EXPIRY_DATE": "2025-11-30", "CONDITION_CODE": "A", "LAST_COUNT_DATE": "2023-12-15", "LAST_ISSUE_DATE": "2024-01-12", "UNIT_COST": 47.50, "TOTAL_VALUE": 116375.00},
        {"WAREHOUSE_ID": "W45G09", "WAREHOUSE_NAME": "ANNISTON ARMY DEPOT - BLDG 401", "MATERIAL_NUM": "000000000050012400", "NSN": "2530-01-595-4455", "DESCRIPTION": "TRACK SHOE, SINGLE PIN T-158LL", "STOCK_TYPE": "UNRS", "QTY_ON_HAND": 1200.000, "QTY_RESERVED": 200.000, "QTY_AVAILABLE": 1000.000, "UOM": "EA", "BIN_LOCATION": "C-08-A-01", "LOT_NUMBER": "LOT-2023-09-4455", "EXPIRY_DATE": None, "CONDITION_CODE": "A", "LAST_COUNT_DATE": "2023-12-15", "LAST_ISSUE_DATE": "2024-01-08", "UNIT_COST": 890.00, "TOTAL_VALUE": 1068000.00},
    ],
    "SHIPMENT_TRACKING": [
        {"SHIPMENT_ID": "SHP-00891234", "SHIP_TYPE": "SURFACE", "TCN": "W45G09-4108-0001", "ORIGIN_DODAAC": "W45G09", "ORIGIN_NAME": "ANNISTON ARMY DEPOT", "DEST_DODAAC": "W45XAA", "DEST_NAME": "2ABCT, 1AD - FORT BLISS", "MATERIAL_NUM": "000000000050012345", "NSN": "2940-01-576-4108", "QUANTITY": 100.000, "WEIGHT_LBS": 245.00, "SHIP_DATE": "2024-01-10", "ETA_DATE": "2024-01-17", "ACTUAL_ARRIVAL": None, "CARRIER": "DLA DISTRIBUTION", "TRACKING_STATUS": "IN_TRANSIT", "PO_REFERENCE": "4500089231", "HAZMAT_CLASS": "NONE"},
        {"SHIPMENT_ID": "SHP-00891200", "SHIP_TYPE": "SURFACE", "TCN": "W45G09-4455-0001", "ORIGIN_DODAAC": "W45G09", "ORIGIN_NAME": "ANNISTON ARMY DEPOT", "DEST_DODAAC": "W45XBB", "DEST_NAME": "DIVARTY, 1AD - FORT BLISS", "MATERIAL_NUM": "000000000050012400", "NSN": "2530-01-595-4455", "QUANTITY": 50.000, "WEIGHT_LBS": 3600.00, "SHIP_DATE": "2024-01-08", "ETA_DATE": "2024-01-15", "ACTUAL_ARRIVAL": "2024-01-14", "CARRIER": "DLA DISTRIBUTION", "TRACKING_STATUS": "DELIVERED", "PO_REFERENCE": "4500089250", "HAZMAT_CLASS": "NONE"},
    ],
}
