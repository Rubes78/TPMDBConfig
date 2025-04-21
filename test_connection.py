import os
import configparser
import pyodbc
from log import log

def test_sql_connection(conn_str):
    try:
        conn = pyodbc.connect(conn_str, timeout=5)
        conn.close()
        return True
    except Exception as e:
        log(f"Connection failed: {e}", level="error")
        return False

def check_required_tables(conn_str, required_tables):
    log("check_required_tables() function called")
    try:
        conn = pyodbc.connect(conn_str, timeout=5)
        cursor = conn.cursor()
        log("Executing table existence check query")
        cursor.execute(
            f"SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME IN ({','.join('?' for _ in required_tables)})",
            required_tables
        )
        found_raw = [row[0] for row in cursor.fetchall()]
        found = {t.lower() for t in found_raw}
        conn.close()

        missing = {t for t in (tbl.lower() for tbl in required_tables) if t not in found}
        if found:
            log(f"Found tables: {', '.join(sorted(found))}")
        if missing:
            log(f"Missing tables: {', '.join(sorted(missing))}")
        return not missing
    except Exception as e:
        log(f"Error checking table existence: {e}", level="error")
        return False

def save_sqlconn_to_creds_ini(conn_str):
    config = configparser.ConfigParser()
    config["SQL"] = {
        "sqlconn": conn_str
    }
    with open("creds.ini", "w") as f:
        config.write(f)
    log("Connection string saved to creds.ini")

if __name__ == "__main__":
    log("Startup check...")

    config = configparser.ConfigParser()
    config.read("configuration.ini")

    try:
        server = config["SQL"]["server"]
        database = config["SQL"]["database"]
        user = config["SQL"]["username"]
        password = config["SQL"]["password"]
    except KeyError as e:
        log(f"Missing configuration key: {e}", level="error")
        exit(1)

    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={user};"
        f"PWD={password};"
        "Encrypt=no;"
    )

    log("Testing initial connection...")
    if test_sql_connection(conn_str):
        log("Initial connection successful.")
        save_sqlconn_to_creds_ini(conn_str)
    else:
        log("Initial connection failed. Skipping creds.ini write.")
        exit(1)

    # Re-verify connection string
    log("Verifying saved connection string from creds.ini...")
    verify_config = configparser.ConfigParser()
    verify_config.read("creds.ini")

    try:
        saved_conn_str = verify_config["SQL"]["sqlconn"]
    except KeyError as e:
        log(f"Missing sqlconn in creds.ini: {e}", level="error")
        exit(1)

    log("Testing connection using saved sqlconn...")
    if test_sql_connection(saved_conn_str):
        log("Verified connection from saved creds.ini")
    else:
        log("Failed to connect using creds.ini")
        exit(1)

    # Force table check always
    log("Now performing required table check...")
    required_tables = ["TPM_Config", "TPM_Items"]
    check_required_tables(saved_conn_str, required_tables)
