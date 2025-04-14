
def load_config_from_db():
    connection = pyodbc.connect(
        f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={DB_SERVER};DATABASE={DB_NAME};UID={DB_USER};PWD={DB_PASSWORD};Encrypt=no;'
    )
    cursor = connection.cursor()
    cursor.execute("SELECT setting_key, setting_value FROM TPM_Config")
    rows = cursor.fetchall()
    config = {row[0]: row[1]for row in rows}
    cursor.close()
    connection.close()
    return config



import os
import csv
import pyodbc
import requests
import configparser
import shutil
import argparse
from datetime import datetime
import time


import configparser

def get_db_credentials():
    ini_path = os.path.join(os.path.expanduser("~"), "TPM_DB_Config", "db.ini")
    config = configparser.ConfigParser()

    if os.path.exists(ini_path):
        config.read(ini_path)
        db_config = config["Database"]
        return db_config["server"], db_config["name"], db_config["user"], db_config["password"]
    else:
        print("🔐 Enter SQL Server connection details:")
        server = input("Server name: ").strip()
        name = input("Database name: ").strip()
        user = input("Username: ").strip()
        password = getpass.getpass("Password: ")

        config["Database"] = {
            "server": server,
            "name": name,
            "user": user,
            "password": password
        }
        os.makedirs(os.path.dirname(ini_path), exist_ok=True)
        with open(ini_path, "w") as configfile:
            config.write(configfile)

        return server, name, user, password

import getpass


# Get SQL Server credentials from db.ini or prompt if missing



LOG_LEVEL = "DEBUG"
DB_SERVER = "localhost"
DB_USER = "sa"
DB_PASSWORD = ""
log_file = ""

def log(message, level="DEBUG"):
    levels = ["DEBUG", "INFO"]
    if levels.index(level) >= levels.index(LOG_LEVEL):
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        msg = f"{timestamp} {message}"
        if log_file:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(msg + "\n")
        print(msg)

def ensure_directory_exists(path):
    os.makedirs(path, exist_ok=True)


def fetch_json(url, params):
    log("Fetching JSON from API...", "INFO")
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def json_to_csv(data, filename):
    if not data:
        log("No data returned from API.", "INFO")
        return
    keys = data[0].keys()
    with open(filename, 'w', newline='', encoding='utf-8') as output_file:
        writer = csv.DictWriter(output_file, keys)
        writer.writeheader()
        writer.writerows(data)
    log(f"CSV backup saved: {filename}", "INFO")

def cast_value(value, expected_type):
    try:
        if value in (None, "", "null"):
            return None
        if expected_type == "int":
            return int(value)
        elif expected_type == "float":
            return float(value)
        elif expected_type == "datetime":
            return datetime.fromisoformat(value)
        else:
            return value
    except Exception as e:
        log(f"Failed to cast value '{value}' as {expected_type}: {e}", "DEBUG")
        return None

def load_existing_barcodes(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT barcode FROM tpm_items")
    existing = {row[0]for row in cursor.fetchall()}
    log(f"Loaded {len(existing)} existing barcodes from tpm_items", "INFO")
    return existing

def create_temp_staging_table(cursor):
    cursor.execute("DROP TABLE IF EXISTS #tpm_items_staging")
    cursor.execute("""
    CREATE TABLE #tpm_items_staging (
        itemID INT,
        lotID INT,
        barcode VARCHAR(255),
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

def insert_with_staging(json_data, DB_NAME, config):
    batch_size = int(config.get("batch_size", "1000"))
    batch_delay = float(config.get("batch_delay", "0.1"))

    connection = pyodbc.connect(
        f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={DB_SERVER};DATABASE={DB_NAME};UID={DB_USER};PWD={DB_PASSWORD};Encrypt=no;'
    )
    existing_barcodes = load_existing_barcodes(connection)
    cursor = connection.cursor()

    columns = [
        ('itemID', 'int'), ('lotID', 'int'), ('barcode', 'str'), ('numberofPieces', 'int'),
        ('productionStoreID', 'int'), ('productionStoreName', 'str'), ('transferStoreID', 'int'),
        ('storeName', 'str'), ('stationID', 'int'), ('stationName', 'str'), ('processorID', 'int'),
        ('processorName', 'str'), ('qtyProduced', 'int'), ('qtySold', 'int'), ('onHand', 'int'),
        ('lastUpdatedDt', 'datetime'), ('departmentID', 'int'), ('department', 'str'),
        ('categoryID', 'int'), ('categoryName', 'str'), ('productionCycleID', 'int'),
        ('productionCycle', 'str'), ('qualityID', 'int'), ('qualityDescr', 'str'),
        ('conditionID', 'int'), ('conditionDescr', 'str'), ('productionStoreCode', 'str'),
        ('transferStoreCode', 'str'), ('price', 'float'), ('subcateogryID', 'int'),
        ('subcategoryName', 'str'), ('subcategoryExtId', 'int'), ('departmentExtId', 'int'),
        ('categoryExtId', 'int'), ('isScanPull', 'str')
    ]

    new_rows = [
        tuple(cast_value(item.get(col), typ) for col, typ in columns)
        for item in json_data if item.get("barcode") not in existing_barcodes
    ]
    total_rows = len(json_data)
    skipped_rows = total_rows - len(new_rows)

    create_temp_staging_table(cursor)

    placeholders = ", ".join(["?"] * len(columns))
    insert_sql = f"INSERT INTO #tpm_items_staging ({', '.join(col for col, _ in columns)}) VALUES ({placeholders})"

    inserted_count = 0
    cursor.fast_executemany = True
    for i in range(0, len(new_rows), batch_size):
        batch = new_rows[i:i + batch_size]
        try:
            cursor.executemany(insert_sql, batch)
            connection.commit()
            inserted_count += len(batch)
            log(f"Inserted batch {i // batch_size + 1} ({len(batch)} records)", "DEBUG")
            time.sleep(batch_delay)
        except pyodbc.Error as e:
            if "1205" in str(e):
                log("Deadlock detected, retrying batch...", "INFO")
                time.sleep(1)
                continue
            else:
                raise

    cursor.execute("""
    MERGE tpm_items WITH (ROWLOCK) AS target
    USING #tpm_items_staging AS source
    ON target.barcode = source.barcode
    WHEN NOT MATCHED BY TARGET THEN
        INSERT (
            itemID, lotID, barcode, numberofPieces, productionStoreID, productionStoreName,
            transferStoreID, storeName, stationID, stationName, processorID, processorName,
            qtyProduced, qtySold, onHand, lastUpdatedDt, departmentID, department,
            categoryID, categoryName, productionCycleID, productionCycle,
            qualityID, qualityDescr, conditionID, conditionDescr,
            productionStoreCode, transferStoreCode, price,
            subcateogryID, subcategoryName, subcategoryExtId, departmentExtId,
            categoryExtId, isScanPull
        )
        VALUES (
            source.itemID, source.lotID, source.barcode, source.numberofPieces, source.productionStoreID, source.productionStoreName,
            source.transferStoreID, source.storeName, source.stationID, source.stationName, source.processorID, source.processorName,
            source.qtyProduced, source.qtySold, source.onHand, source.lastUpdatedDt, source.departmentID, source.department,
            source.categoryID, source.categoryName, source.productionCycleID, source.productionCycle,
            source.qualityID, source.qualityDescr, source.conditionID, source.conditionDescr,
            source.productionStoreCode, source.transferStoreCode, source.price,
            source.subcateogryID, source.subcategoryName, source.subcategoryExtId, source.departmentExtId,
            source.categoryExtId, source.isScanPull
        );
    """)
    final_inserted = cursor.rowcount
    connection.commit()

    cursor.close()
    connection.close()
    return final_inserted, skipped_rows, total_rows


# Get DB credentials early so they are available for all functions
DB_SERVER, DB_NAME, DB_USER, DB_PASSWORD = get_db_credentials()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-daterange", help="Date range override in MM/DD/YY-MM/DD/YY format")
    parser.add_argument("-nocsv", action="store_true", help="Skip CSV backup")
    args = parser.parse_args()

    base_dir = os.path.join(os.path.expanduser("~"), "TPM_DB_Config")
    data_dir = os.path.join(base_dir, "Data")
    processed_dir = os.path.join(data_dir, "Processed")
    duplicates_dir = os.path.join(data_dir, "Duplicates")
    ensure_directory_exists(data_dir)
    ensure_directory_exists(processed_dir)
    ensure_directory_exists(duplicates_dir)
    ini_path = os.path.join(base_dir, "Import.ini")

    config = load_config_from_db()
    db_name = config["db_name"]
    LOG_LEVEL = config.get("db_logLevel", "INFO").upper()
    log_file = os.path.join(base_dir, "TPM.log")
    params = {
        "userName": config["api_userName"],
        "password": config["api_password"],
        "companyID": config["api_companyID"]
    }

    
    
    
    
    if args.daterange:
        try:
            import re
            daterange_input = args.daterange.strip()

            # Auto-correct if it looks like two full dates joined by a single dash
            if re.fullmatch(r'\d{1,2}-\d{1,2}-\d{2,4}-\d{1,2}-\d{1,2}-\d{2,4}', daterange_input):
                # Split into two 3-part dates using the position
                parts = daterange_input.split("-")
                start_str = "/".join(parts[:3])
                end_str = "/".join(parts[3:])
            elif ' to ' in daterange_input:
                start_str, end_str = daterange_input.split(' to ')
            elif ' -- ' in daterange_input:
                start_str, end_str = daterange_input.split(' -- ')
            elif '/' in daterange_input and '-' in daterange_input:
                start_str, end_str = daterange_input.split('-')
            else:
                raise ValueError("Ambiguous date format. Use slashes or a separator like ' to ' or ' -- '")

            start_str = start_str.strip().replace("-", "/")
            end_str = end_str.strip().replace("-", "/")

            for fmt in ("%m/%d/%Y", "%m/%d/%y", "%-m/%-d/%Y", "%-m/%-d/%y"):
                try:
                    start = datetime.strptime(start_str, fmt)
                    end = datetime.strptime(end_str, fmt)
                    break
                except ValueError:
                    continue
            else:
                raise ValueError
            params["Updatestartdt"] = start.strftime("%Y-%m-%d 00:00:00")
            params["Updateenddt"] = end.strftime("%Y-%m-%d 23:59:59")
            timestamp_now = f"{start.strftime('%Y%m%d')}_to_{end.strftime('%Y%m%d')}"
        except ValueError:
            print("Invalid date format. Use MM/DD/YY or MM/DD/YYYY with a separator like ' to ', ' -- ', or a valid two-date range.")
            exit(1)
    else:
        timestamp_now = datetime.now().strftime("%m%d%y_%H%M%S")





    if not args.nocsv:
        filename = os.path.join(data_dir, f"TPMData-{timestamp_now}.csv")
        log(f"Downloading data to {filename}", "DEBUG")
    else:
        pass

    url = "http://tpmapi-prd.rcsaero.com/RcsItems"
    json_data = fetch_json(url, params)
    if not json_data:
        log("No data to download for the given date range.", "INFO")
        print("No data to download.")
        exit(0)

    if not args.nocsv:
        json_to_csv(json_data, filename)
    else:
        log("CSV backup skipped due to -nocsv flag.", "INFO")

    start_time = datetime.now()
    inserted, skipped_rows, total_rows = insert_with_staging(json_data, db_name, config)

    if not args.nocsv:
        if inserted > 0:
            shutil.move(filename, os.path.join(processed_dir, os.path.basename(filename)))
            log(f"Moved processed file to: {os.path.join(processed_dir, os.path.basename(filename))}", "INFO")
        else:
            shutil.move(filename, os.path.join(duplicates_dir, os.path.basename(filename)))
            log("No new rows inserted. File moved to Duplicates.", "INFO")
    else:
        log("File move skipped due to -nocsv flag.", "INFO")

    duration = datetime.now() - start_time
    log("\nIMPORT SUMMARY\n" + "-"*28, "INFO")
    log(f"Total rows from API:        {total_rows}", "INFO")
    log(f"Inserted new rows:          {inserted}", "INFO")
    log(f"Skipped duplicates:         {skipped_rows}", "INFO")
    if not args.nocsv:
        log(f"File moved to:              {'Processed/' if inserted > 0 else 'Duplicates/'}", "INFO")
    else:
        log("File move skipped due to -nocsv flag.", "INFO")
    log(f"Duration:                   {duration}", "INFO")

    print("Import complete.")
