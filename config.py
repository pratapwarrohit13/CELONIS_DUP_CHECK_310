# Configuration Registry for Enterprise Duplicate Checker

ERP_CONFIG = {
    "SAP": {
        "AP": {
            "description": "Accounts Payable (BSIK/BSAK/BKPF/BSEG)",
            "tables": ["BKPF", "BSEG"],
            "join_keys": ["MANDT", "BUKRS", "BELNR", "GJAHR"],
            "duplicate_keys": ["MANDT", "BUKRS", "LIFNR", "XBLNR", "BLDAT", "WRBTR", "WAERS"],
            "fallback_tables": ["BSIK", "BSAK"], # If Header/Segment not found
            "fallback_join_keys": ["MANDT", "BUKRS", "LIFNR", "BELNR", "GJAHR"],
            "fallback_duplicate_keys": ["MANDT", "BUKRS", "LIFNR", "XBLNR", "BLDAT", "DMBTR", "WAERS"]
        },
        "PROCUREMENT": {
            "description": "Procurement (EKKO/EKPO)",
            "tables": ["EKKO", "EKPO"],
            "join_keys": ["MANDT", "EBELN"],
            "duplicate_keys": ["MANDT", "LIFNR", "MATNR", "MENGE", "BEDAT"] # Vendor, Material, Qty, Order Date
        },
        "AR": {
            "description": "Accounts Receivable (VBRK/VBRP)",
            "tables": ["VBRK", "VBRP"],
            "join_keys": ["MANDT", "VBELN"],
            "duplicate_keys": ["MANDT", "KUNAG", "XBLNR", "FKDAT", "NETWR"] # Payer, Ref, Bill Date, Net Value
        }
    },
    "ORACLE": {
         "AP": {
            "description": "Accounts Payable (AP_INVOICES_ALL)",
            "tables": ["AP_INVOICES_ALL", "AP_INVOICE_LINES_ALL"],
            "join_keys": ["INVOICE_ID"],
            "duplicate_keys": ["VENDOR_ID", "INVOICE_NUM", "INVOICE_DATE", "INVOICE_AMOUNT"]
        }
    },
    "COUPA": {
        "AP": {
            "description": "Coupa Invoices",
            "tables": ["Invoices", "InvoiceLines"],
            "join_keys": ["ID", "InvoiceID"], # Hypothetical join, depends on export
            "duplicate_keys": ["InvoiceNumber", "Supplier", "Total", "InvoiceDate"]
        }
    }
}
