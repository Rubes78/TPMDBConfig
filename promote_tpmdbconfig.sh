#!/bin/bash

echo "📂 Promoting ~/TPM_DB_Config ➜ ~/GitHub/TPMDBConfig..."

# Ensure target exists
mkdir -p ~/GitHub/TPMDBConfig

# Sync files from working folder to git folder
cp ~/TPM_DB_Config/import.py ~/GitHub/TPMDBConfig/
cp ~/TPM_DB_Config/run_import.sh ~/GitHub/TPMDBConfig/
cp ~/TPM_DB_Config/requirements.txt ~/GitHub/TPMDBConfig/ 2>/dev/null || true
cp ~/TPM_DB_Config/setup.sh ~/GitHub/TPMDBConfig/ 2>/dev/null || true
cp ~/TPM_DB_Config/README.md ~/GitHub/TPMDBConfig/ 2>/dev/null || true

cd ~/GitHub/TPMDBConfig || exit

git add .
git commit -m "Promote DB-config update (2025-04-14 12:55:42)"
git push origin main

echo "✅ TPM DB-config version pushed to GitHub."
