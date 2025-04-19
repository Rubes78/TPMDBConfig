import argparse
import getpass
import pyodbc
import socket
import configparser
import os
from datetime import datetime as dt
from log import setup_logger, log

setup_logger("DBCreate")


def run_sql_setup():
    while True:
        server = input("Server name: ").strip()
        if is_sql_server_reachable(server):
            log(f"Server '{server}' is reachable on port 1433.")
            break
        else:
            log(f"Server '{server}' is not reachable on port 1433. Try again.")

    while True:
        dbname = input("Database name: ").strip()
        if dbname:
            break
        log("Database name cannot be empty.")

    while True:
        user = input("Username: ").strip()
        if user:
            break
        log("Username cannot be empty.")

    while True:
        password = getpass.getpass("Password: ")
        if password:
            break
        log("Password cannot be empty.")

    while True:
        try:
            conn = pyodbc.connect(
                f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE=master;UID={user};PWD={password};Encrypt=no;',
                timeout=5
            )
            conn.autocommit = True
            break
        except pyodbc.Error as e:
            if e.args and e.args[0] == '28000':
                log("Login failed. Please try again.")
                user = input("Username: ").strip()
                password = getpass.getpass("Password: ")
            else:
                log(f"SQL Setup failed: {e}")
                exit(1)

    try:
        cursor = conn.cursor()
        cursor.execute(f"IF DB_ID('{dbname}') IS NULL CREATE DATABASE [{dbname}]")
        log(f"Database '{dbname}' verified or created.")

        config = configparser.ConfigParser()
        config["SQL"] = {
            "server": server,
            "database": dbname,
            "username": user,
            "password": password
        }
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "configuration.ini")
        with open(config_path, "w") as f:
            config.write(f)
        log("Configuration saved to configuration.ini")

        conn.close()

        conn = pyodbc.connect(
            f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={dbname};UID={user};PWD={password};Encrypt=no;',
            timeout=5
        )
        cursor = conn.cursor()
        cursor.execute("""
        IF NOT EXISTS (
            SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'TPM_Config'
        )
        CREATE TABLE TPM_Config (
            setting_key VARCHAR(100) PRIMARY KEY,
            setting_value NVARCHAR(1000)
        )
        """)
        cursor.execute("""
        IF NOT EXISTS (
            SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'tpm_items'
        )
        CREATE TABLE tpm_items (
            itemID INT,
            lotID INT,
            barcode VARCHAR(255) PRIMARY KEY,
            numberofPieces INT,
            productionStoreID INT,
            productionStoreName VARCHAR(255),
            transferStoreID INT,
            storeName VARCHAR(255),
            stationID INT,
            stationName VARCHAR(255),
            processorID INT,
            processorName VARCHAR(255),
            qtyProduced INT,
            qtySold INT,
            onHand INT,
            lastUpdatedDt DATETIME,
            departmentID INT,
            department VARCHAR(255),
            categoryID INT,
            categoryName VARCHAR(255),
            productionCycleID INT,
            productionCycle VARCHAR(255),
            qualityID INT,
            qualityDescr VARCHAR(255),
            conditionID INT,
            conditionDescr VARCHAR(255),
            productionStoreCode VARCHAR(255),
            transferStoreCode VARCHAR(255),
            price FLOAT,
            subcateogryID INT,
            subcategoryName VARCHAR(255),
            subcategoryExtId INT,
            departmentExtId INT,
            categoryExtId INT,
            isScanPull NVARCHAR(10)
        )
        """)
        conn.commit()
        log("Tables verified or created.")
        conn.close()
        exit(0)

    except pyodbc.Error as e:
        log(f"SQL Setup failed during table creation: {e}")
        exit(1)


def is_sql_server_reachable(server, port=1433, timeout=2):
    try:
        with socket.create_connection((server, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Force SQL setup, skipping configuration.ini check")
    args = parser.parse_args()

    log("SQL setup mode...")

    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "configuration.ini")
    continue_full_setup = False
    skip_ini_validation = False

    if args.force:
        log("Force mode enabled. This will skip configuration checks and may overwrite existing database and settings.")
        confirm_force = input("Are you sure you want to continue? (y/n): ").strip().lower()
        if confirm_force != 'y':
            log("User cancelled forced setup. Exiting.")
            exit(0)
        log("Proceeding with forced SQL setup.")
        continue_full_setup = True
        skip_ini_validation = True

    if not skip_ini_validation and os.path.exists(config_path):
        config = configparser.ConfigParser()
        config.read(config_path)
        existing_server = config.get("SQL", "server", fallback="UNKNOWN")
        existing_db = config.get("SQL", "database", fallback="UNKNOWN")
        user = config.get("SQL", "username", fallback=None)
        password = config.get("SQL", "password", fallback=None)

        log(f"SQL Setup has already been run for server '{existing_server}' and database '{existing_db}'.")

        try:
            conn = pyodbc.connect(
                f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={existing_server};DATABASE={existing_db};UID={user};PWD={password};Encrypt=no;',
                timeout=5
            )
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'TPM_Config'")
            cursor.fetchone()
            cursor.execute("SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'tpm_items'")
            cursor.fetchone()

            log("Connection successful and required tables exist.")
            response = input("SQL setup appears complete. Do you still want to proceed with setup? (y/n): ").strip().lower()
            if response != 'y':
                log("User chose to skip re-running SQL setup. Exiting.")
                exit(0)
            log("User chose to proceed with SQL setup.")
            run_sql_setup()
            exit(0)
        except Exception as e:
            log(f" Unable to validate configuration: {e}")
            log("Proceeding with full setup...")
            continue_full_setup = True
    else:
        continue_full_setup = True

    if not continue_full_setup:
        exit(0)

    run_sql_setup()
