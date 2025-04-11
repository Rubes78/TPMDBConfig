TPM Optimized Importer
======================

This version:
- Downloads JSON from the TPM API
- Saves a CSV backup to ~/TPM/Data
- Imports data directly into a SQL staging table
- Deduplicates and inserts new records into tpm_items
- Moves the CSV to Processed only if SQL import is successful
- Logs every step for easy debugging

📦 Setup Instructions:
1. Unzip this archive
2. Run setup:
   chmod +x setup.sh
   ./setup.sh

➡️ To run the import:
   source venv/bin/activate
   ./run_import.sh

📝 Logs and data will be stored in ~/TPM
