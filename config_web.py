from flask import Flask, request, render_template, redirect, make_response
import os
import configparser
import pyodbc
from log import log
import logging
import time

# Disable console logging only for config_web
logger = logging.getLogger("config_web")
for handler in logger.handlers[:]:
    if isinstance(handler, logging.StreamHandler):
        logger.removeHandler(handler)
import logging

# Disable console logging for this module only
logger = logging.getLogger("config_web")
for handler in logger.handlers:
    if isinstance(handler, logging.StreamHandler):
        logger.removeHandler(handler)


def get_eth0_ip():
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        log(f"Failed to detect eth0 IP: {e}")
        return "127.0.0.1"

app = Flask(__name__)

CONFIG_FIELDS = [
    "API_URL",
    "userName",
    "password",
    "companyID",
    "LOG_LEVEL",
    "BASE_DIR"
]

def create_connection():
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), "configuration.ini"))

    server = config.get("SQL", "server")
    database = config.get("SQL", "database")
    user = config.get("SQL", "username")
    password = config.get("SQL", "password")

    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={server};DATABASE={database};UID={user};PWD={password};Encrypt=no;"
    )
    conn = pyodbc.connect(conn_str)
    return conn, server, database

def ensure_config_fields(conn):
    cursor = conn.cursor()
    existing_keys = set()
    try:
        cursor.execute("SELECT setting_key FROM TPM_Config")
        existing_keys = {row.setting_key for row in cursor.fetchall()}
    except Exception as e:
        log(f"Could not fetch existing keys: {e}")

    for field in CONFIG_FIELDS:
        if field not in existing_keys:
            log(f"Inserting missing config field: {field}")
            cursor.execute("INSERT INTO TPM_Config (setting_key, setting_value) VALUES (?, '')", field)
    conn.commit()
    cursor.close()

def load_config_values():
    values = {}
    try:
        conn, _, _ = create_connection()
        ensure_config_fields(conn)
        cursor = conn.cursor()
        cursor.execute("SELECT setting_key, setting_value FROM TPM_Config")
        rows = cursor.fetchall()
        values = {row.setting_key: row.setting_value for row in rows}
        cursor.close()
        conn.close()
    except Exception as e:
        log(f"Failed to load existing config: {e}")
    return values

@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/", methods=["GET", "POST"])
def config_form():
    message = ""
    success = True
    values = load_config_values()

    try:
        conn, server, database = create_connection()
        ensure_config_fields(conn)
    except Exception as e:
        return f"Database connection error: {e}", 500

    if request.method == "POST":
        try:
            cursor = conn.cursor()
            for field in CONFIG_FIELDS:
                value = request.form.get(field, "")
                log(f"Processing field update: {field} = {value}")
                cursor.execute(
                    "UPDATE TPM_Config SET setting_value = ? WHERE setting_key = ?; "
                    "IF @@ROWCOUNT = 0 INSERT INTO TPM_Config (setting_key, setting_value) VALUES (?, ?);",
                    (value, field, field, value)
                )
            conn.commit()
            cursor.close()
            log("Web config updated successfully.")
            return redirect("/?saved=1")
        except Exception as e:
            message = "Error: " + str(e)
            log(f"Web config update failed: {e}")
            success = False

    if request.args.get("saved") == "1":
        message = "Configuration updated."
        values = load_config_values()

    log(f"Request: {request.method} /")
    response = make_response(render_template("config_form.html", values=values, message=message, success=success, sql_info={"server": server, "database": database}))
    log("Response: 200 OK")
    return response


if __name__ == "__main__":
    import sys
    import subprocess
    import os

    if '--background' not in sys.argv:
        host_ip = get_eth0_ip()
        print(f"Go to http://{host_ip}:5050 for further configuration setup.")
        subprocess.Popen([sys.executable, os.path.abspath(__file__), '--background'],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        sys.exit(0)

    host_ip = get_eth0_ip()
    try:
        log("Checking for other config_web.py processes...")
        current_pid = os.getpid()
        result = subprocess.run(["pgrep", "-f", "config_web.py"], capture_output=True, text=True)
        pids = [int(pid) for pid in result.stdout.split() if pid.strip().isdigit()]
        other_pids = [pid for pid in pids if pid != current_pid]
        for pid in other_pids:
            os.kill(pid, 9)
            log(f"Terminated existing config_web.py process: PID {pid}")
        if other_pids:
            log("Waiting briefly for port to free...")
            import time
            time.sleep(1)
        else:
            log("No other config_web.py processes found.")
    except Exception as e:
        log(f"Could not clean up config_web.py processes: {e}", level="warning")

    log("Web config server starting silently in background")
    try:
        log(f"Launching Flask app on http://{host_ip}:5050")
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')
        app.run(host=host_ip, port=5050, debug=False)
    except Exception as e:
        log(f"Flask failed to start: {e}", level="error")