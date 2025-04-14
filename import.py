import argparse
import configparser
import csv
import datetime
import getpass
import json
import os
import pyodbc
import requests
import sys
from datetime import datetime as dt

def log(message, level="INFO"):
    print(f"[{dt.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-sql", action="store_true", help="Setup SQL environment")
    args = parser.parse_args()

    if args.sql:
        print("🔧 SQL setup mode...")
        server = input("Server name: ").strip()
        dbname = input("Database name: ").strip()
        user = input("Username: ").strip()
        password = getpass.getpass("Password: ")

        try:
            conn = pyodbc.connect(
                f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE=master;UID={user};PWD={password};Encrypt=no;',
                timeout=5
            )
            conn.autocommit = True
            cursor = conn.cursor()
            cursor.execute(f"IF DB_ID('{dbname}') IS NULL CREATE DATABASE [{dbname}]")
            print(f"✅ Database '{dbname}' verified or created.")
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
            print("✅ Tables verified or created.")
            conn.close()
            exit(0)

        except pyodbc.Error as e:
            print(f"❌ SQL Setup failed: {e}")
            exit(1)
