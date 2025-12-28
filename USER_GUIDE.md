# User Guide: Celonis Enterprise Duplicate Checker

This guide provides detailed instructions on how to set up, run, and verify the Celonis Enterprise Duplicate Checker specifically for SAP, Oracle, and Coupa environments.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Configuration](#configuration)
3. [Running the Tool](#running-the-tool)
4. [Duplicate Logic Explained](#duplicate-logic-explained)
5. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before running the tool, ensure you have:
*   **Python 3.8+** installed.
*   **Access to Celonis EMS** (Team URL and API Token).
*   **Permissions** to Edit Data Pools (`EDIT_DATA_POOL`, `CREATE_DATA_POOL`).

## Configuration

1.  **Environment Variables**:
    Create a `.env` file in the project root with the following keys:
    ```env
    CELONIS_URL=https://your-team.training.celonis.cloud
    CELONIS_API_TOKEN=your_api_token_here
    DATA_POOL_ID=optional_pool_id
    ```
    *Note: If `DATA_POOL_ID` is left empty, the tool will prompt you to select one from a list.*

2.  **ERP Configuration (`config.py`)**:
    The tool comes pre-configured with standard tables and keys for:
    *   **SAP**: `BKPF`, `BSEG`, `EKKO`, `EKPO`, `VBRK`, `VBRP`
    *   **Oracle**: `AP_INVOICES_ALL`
    *   **Coupa**: `Invoices`
    
    *If you have custom tables, you can add them to `config.py` or select "Custom (Manual Entry)" when running the tool.*

## Running the Tool

1.  Open your terminal or command prompt.
2.  Navigate to the project directory.
3.  Run the script:
    ```bash
    python main.py
    ```
4.  **Follow the Prompts**:
    *   **Select Data Pool**: Choose the target Data Pool containing your source tables.
    *   **Select ERP System**: Enter the number corresponding to your ERP (e.g., `1` for SAP).
    *   **Select Process**: Choose the business process (e.g., `1` for Accounts Payable).
    *   **Filter Frequeny**: Choose how you want to define a "duplicate" timeframe (e.g., `all` for anytime, or `month` for duplicates within the same month).
    *   **Target Table**: Enter the name of the table to create/append in Celonis (e.g., `DUPLICATE_RESULTS`).

## Duplicate Logic Explained

The tool identifies duplicates based on **business keys**, not just row identity.

### SAP Accounts Payable (AP) example:
*   **Join**: `BKPF` (Header) and `BSEG` (Segment) are joined on `MANDT`, `BUKRS`, `BELNR`, and `GJAHR`.
*   **Duplicate Criteria**: Two records are considered duplicates if they share the same:
    *   `MANDT` (Client)
    *   `BUKRS` (Company Code)
    *   `LIFNR` (Vendor)
    *   `XBLNR` (Reference Document Number)
    *   `BLDAT` (Document Date)
    *   `WRBTR` (Amount)
    *   `WAERS` (Currency)
    
    *This implies that the same vendor issued two invoices with the same reference number, date, and amount, which is a classic potential double detection.*

## Troubleshooting

*   **"No tables found"**: Ensure your Data Pool actually contains the standard tables (e.g., `BKPF`). If using a temporary Data Model, ensure the connection is valid.
*   **Login Failed**: Check your `.env` file for typos in the API Token or URL.
*   **Push Failed**: Verify you have write permissions to the Data Pool. The tool will try to append if the table exists, or create a new one if it doesn't.
