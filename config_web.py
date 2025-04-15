import os
import sys
import subprocess
import time
from flask import Flask, render_template, request

def create_connection():
    try:
        import pyodbc
        from log import log
        import configparser
        import os

        config = configparser.ConfigParser()
        ini_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "configuration.ini")
        config.read(ini_path)

        server = config.get("SQL", "server")
        database = config.get("SQL", "database")
        user = config.get("SQL", "username")
        password = config.get("SQL", "password")

        conn_str = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={server};DATABASE={database};UID={user};PWD={password};Encrypt=no;"
        )
        conn = pyodbc.connect(conn_str)
        return conn

    except Exception as e:
        log(f"Error in create_connection: {e}")
        raise

import configparser
import pyodbc
from log import setup_logger, log

setup_logger("WebConfig")
app = Flask(__name__)

@app.before_request
def log_request_info():
    log(f"Request: {request.method} {request.path}")

@app.after_request
def log_response_info(response):
    log(f"Response: {response.status}")
    return response

# Fields to be populated in TPM_Config
CONFIG_FIELDS = [
    "API_URL",
    "API_TOKEN",
    "COMP_ID",
    "LOG_LEVEL",
    "BASE_DIR"
]
@app.route("/", methods=["GET", "POST"])
def config_form():
    values = {}
    message = ""
    success = True

    if request.method == "POST":
        try:
            conn = create_connection()
            cursor = conn.cursor()
            for key in CONFIG_FIELDS:
                val = request.form.get(key, "")
                values[key] = val
                cursor.execute("""
                    MERGE TPM_Config AS target
                    USING (SELECT ? AS setting_key, ? AS setting_value) AS source
                    ON target.setting_key = source.setting_key
                    WHEN MATCHED THEN
                        UPDATE SET setting_value = source.setting_value
                    WHEN NOT MATCHED THEN
                        INSERT (setting_key, setting_value)
                        VALUES (source.setting_key, source.setting_value);
                """, key, val)
            conn.commit()
            message = "Configuration saved successfully."
            log("Configuration values updated via web interface.")
        except Exception as e:
            success = False
            message = f"Error: {e}"
            log(f"Web config update failed: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
    else:
        try:
            conn = create_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT setting_key, setting_value FROM TPM_Config")
            rows = cursor.fetchall()
            for row in rows:
                values[row.setting_key] = row.setting_value
        except Exception as e:
            log(f"Failed to load existing config: {e}")
            message = "Could not load current values."
            success = False
        finally:
            if 'conn' in locals():
                conn.close()

    return render_template("config_form.html", fields=CONFIG_FIELDS, values=values, message=message, success=success)

if __name__ == "__main__":
    if os.environ.get("FLASK_BACKGROUND") != "1":
        script_path = os.path.abspath(sys.argv[0])
        log(f"Launching config_web.py in background from: {script_path}")
        try:
            env = os.environ.copy()
            env["FLASK_BACKGROUND"] = "1"
            subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=env,
                close_fds=True
            )
            time.sleep(1)
        except Exception as e:
            log(f"Background launch failed: {e}")
        sys.exit(0)
    app.run(host='0.0.0.0', port=5050, debug=True)

@app.route("/", methods=["GET", "POST"])
def config_form():
    conn = create_connection()
    cursor = conn.cursor()

    values = {}
    message = ""
    success = True

    if request.method == "POST":
        for field in CONFIG_FIELDS:
            value = request.form.get(field, "")
            cursor.execute("""
                MERGE TPM_Config AS target
                USING (SELECT ? AS FieldName, ? AS FieldValue) AS source
                ON target.FieldName = source.FieldName
                WHEN MATCHED THEN UPDATE SET FieldValue = source.FieldValue
                WHEN NOT MATCHED THEN INSERT (FieldName, FieldValue) VALUES (source.FieldName, source.FieldValue);
            """, (field, value))
        conn.commit()
        message = "Configuration updated."
        success = True
    else:
        try:
            cursor.execute("SELECT FieldName, FieldValue FROM TPM_Config")
            rows = cursor.fetchall()
            values = {row.FieldName: row.FieldValue for row in rows}
            log(f"Loaded {len(values)} config value(s) from TPM_Config")
        except Exception as e:
            log(f"Error loading config values: {e}")
            message = "Unable to load existing values. Table may be missing or empty."
            success = False
        rows = cursor.fetchall()
        values = {row.FieldName: row.FieldValue for row in rows}

    cursor.close()
    conn.close()

    return render_template("config_form.html", fields=CONFIG_FIELDS, values=values, message=message, success=success)