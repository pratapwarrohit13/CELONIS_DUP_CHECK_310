# Celonis Enterprise Duplicate Checker

## Overview
This tool is an advanced, enterprise-ready Python application designed to identify and manage duplicate records within Celonis processes. It specifically supports **SAP**, **Oracle EBS**, and **Coupa** environments, with pre-configured logic for **Accounts Payable (AP)**, **Procurement**, and **Accounts Receivable (AR)**.

## Key Features
- **Multi-ERP Support**: Native support for SAP (`BKPF`/`BSEG`), Oracle, and Coupa.
- **Intelligent Logic**: Uses process-specific keys (e.g., `MANDT, BUKRS, BELNR, GJAHR`) for accurate table joins and duplicate detection.
- **Flexible Filtering**: Allows filtering duplicates by time frequency (Hour, Day, Week, Month, or All).
- **Data Write-Back**: Automatically pushes identified duplicates back to a Celonis Data Pool table for analysis.
- **Robustness**: Includes fallback mechanisms for Data Model creation and PQL-based data extraction.

## Prerequisites
- Python 3.8+
- A Celonis Execution Management System (EMS) account.
- An API Token with `EDIT_DATA_POOL` permissions.

## Installation
1.  Clone this repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Configure your environment:
    - Rename `.env.template` to `.env`.
    - Fill in your `CELONIS_URL`, `CELONIS_API_TOKEN`, and `DATA_POOL_ID`.

## Quick Start
Run the main application:
```bash
python main.py
```
Follow the interactive prompts to select your Data Pool, ERP System, and Process.

-----
*For detailed usage instructions, please refer to [USER_GUIDE.md](USER_GUIDE.md).*
