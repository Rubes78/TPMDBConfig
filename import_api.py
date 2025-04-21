
import configparser
import pyodbc
import requests
import argparse
from datetime import datetime
from log import log

def load_sql_credentials():
    config = configparser.ConfigParser()
    config.read("creds.ini")
    try:
        conn_str = config["SQL"]["sqlconn"]
        return pyodbc.connect(conn_str, timeout=5)
    except Exception as e:
        log(f"Failed to connect to SQL: {e}", level="error")
        exit(1)

def load_api_config(cursor):
    cursor.execute("SELECT setting_key, setting_value FROM TPM_Config")
    rows = cursor.fetchall()
    return {row[0]: row[1] for row in rows}

def fetch_api_data(config, date_range=None):
    url = config.get("API_URL")
    if not url:
        log("API_URL not found in TPM_Config", level="error")
        exit(1)

    params = {
        "userName": config.get("userName"),
        "password": config.get("password"),
        "companyID": config.get("companyID")
    }

    if date_range:
        try:
            start_str, end_str = date_range.split("-")
            start_date = datetime.strptime(start_str.strip(), "%m/%d/%y")
            end_date = datetime.strptime(end_str.strip(), "%m/%d/%y")
            params["Updatestartdt"] = start_date.strftime("%Y-%m-%d 00:00:00")
            params["Updateenddt"] = end_date.strftime("%Y-%m-%d 23:59:59")
            log(f"Date range override: {params['Updatestartdt']} to {params['Updateenddt']}")
        except Exception as e:
            log(f"Invalid date range format. Use MM/DD/YY-MM/DD/YY: {e}", level="error")
            exit(1)

    try:
        log(f"Sending API request to: {url}")
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        log(f"API call failed: {e}", level="error")
        exit(1)

def infer_sql_schema(record):
    schema = {}
    for key, value in record.items():
        if isinstance(value, int):
            schema[key] = "INT"
        elif isinstance(value, float):
            schema[key] = "FLOAT"
        elif isinstance(value, bool):
            schema[key] = "BIT"
        elif isinstance(value, str) and len(value) > 500:
            schema[key] = "NVARCHAR(MAX)"
        else:
            schema[key] = "NVARCHAR(255)"
    return schema

def create_table_if_needed(cursor, table_name, schema):
    sql = f"""
    IF NOT EXISTS (
        SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = '{table_name}'
    )
    BEGIN
        CREATE TABLE {table_name} (
            {', '.join([f"[{col}] {dtype}" for col, dtype in schema.items()])}
        )
    END
    """
    cursor.execute(sql)
    log(f"Verified or created table: {table_name}")

def insert_api_data(cursor, table_name, data, schema):
    columns = list(schema.keys())
    placeholders = ", ".join(["?"] * len(columns))
    insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
    values = []
    for record in data:
        row = [record.get(col) for col in columns]
        values.append(row)
    cursor.executemany(insert_sql, values)
    log(f"Inserted {len(values)} rows into {table_name}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-daterange", help="Optional date range MM/DD/YY-MM/DD/YY")
    args = parser.parse_args()

    log("import_api.py startup...")

    conn = load_sql_credentials()
    cursor = conn.cursor()

    config = load_api_config(cursor)
    data = fetch_api_data(config, args.daterange)

    if not isinstance(data, list) or not data:
        log("API returned no usable data.", level="warning")
        return

    schema = infer_sql_schema(data[0])
    table_name = "APIItems"

    create_table_if_needed(cursor, table_name, schema)
    insert_api_data(cursor, table_name, data, schema)

    conn.commit()
    cursor.close()
    conn.close()

    log("Import process complete.")

if __name__ == "__main__":
    main()
