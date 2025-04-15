# TPMDBConfig

## Overview
This module is responsible for setting up the SQL Server database and required tables for the TPM import process. It creates a configuration file (`configuration.ini`) for storing connection credentials and ensures the necessary SQL structure is in place.

---

## `dbcreate.py`

### Features
- ✅ Prompts for server, database, and credentials if no config exists
- ✅ Validates existing `configuration.ini` settings and skips setup if valid
- ✅ Prompts the user to proceed if a valid configuration already exists
- ✅ Supports `--force` to skip validation and re-run setup
- ✅ Logs all activity to `AppLog.log` using the tag `DBCreate`

---

### Usage

#### Run Setup Normally:
```bash
python3 dbcreate.py -sql
```

- If no config exists, it walks through setup.
- If config exists and is valid, you'll be prompted:
  ```
  SQL setup appears complete. Do you still want to proceed with setup? (y/n):
  ```

#### Force Setup Regardless:
```bash
python3 dbcreate.py -sql --force
```

- Skips validation, warns user, and runs setup fresh.

---

### Logging
All logs go to `AppLog.log` in the project root. They include timestamps and the source module:
```
[2025-04-15 14:25:34] DBCreate | INFO: Database verified or created.
```

---

### Files Generated
- `configuration.ini`: stores verified SQL connection settings
- `AppLog.log`: unified application log file

---

## Version
Current: `v1.1-dbsetup`
