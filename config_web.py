import os
import sys
import subprocess
import time
from flask import Flask, render_template, request
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
    "api_url",
    "auth_token",
    "client_id",
    "log_level",
    "batch_size",
    "delay_seconds"
]

def get_db_connection():
    config = configparser.ConfigParser()
    config.read("configuration.ini")
    server = config.get("SQL", "server")
    db = config.get("SQL", "database")
    user = config.get("SQL", "username")
    pwd = config.get("SQL", "password")
    conn = pyodbc.connect(
        f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={db};UID={user};PWD={pwd};Encrypt=no;",
        timeout=5
    )
    return conn

@app.route("/", methods=["GET", "POST"])
def config_form():
    values = {}
    message = ""
    success = True

    if request.method == "POST":
        try:
            conn = get_db_connection()
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
            conn = get_db_connection()
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
