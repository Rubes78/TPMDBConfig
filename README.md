# TPMDBConfig

This project contains the **database creation and configuration module** for the TPM data import system. It sets up the SQL Server database, creates required tables, and initializes logging.

---

## 📁 Project Structure

| File              | Description |
|-------------------|-------------|
| `dbcreate.py`     | Interactive script that verifies SQL Server, creates the database and tables, and sets logging config. |
| `log.py`          | Modular logger that writes to `AppLog.log` and tags each message by module (e.g. DBCreate). |
| `AppLog.log`      | Unified application log file. |
| `requirements.txt`| Dependencies for the Python environment (`pyodbc`, `requests`, etc.). |
| `setup.sh`        | Bootstraps the virtual environment and installs required packages. |
| `run_import.sh`   | Shell wrapper for launching the future import module. |

---

## 🚀 Usage

### 1. Setup Environment
```bash
./setup.sh
```

### 2. Create Database
```bash
python3 dbcreate.py -sql
```

You will be prompted for:
- SQL Server name
- Database name
- Username / password

The script will:
- Verify server connectivity
- Create the DB if it doesn't exist
- Create required tables (`TPM_Config`, `tpm_items`)
- Set log level to `DEBUG` by default

---

## 🧾 Logging

- Logs are saved to `AppLog.log` in the same directory.
- Tagged per module (e.g., `DBCreate | INFO`).
- Logging level can be controlled via the `TPM_Config` table.

---

## 🏁 Version

**v1-dbsetup**  
This version finalizes the database setup module and unified logging system.

