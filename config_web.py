from flask import Flask, request, render_template, redirect, make_response
import os
import configparser
import pyodbc
from log import log


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
    "API_TOKEN",
    "API_ID",
    "API_USER",
    "COMP_ID",
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
    log(f"Launching config_web.py in background from: {os.path.abspath(__file__)}")
    import subprocess, sys
    if "--background" not in sys.argv:
        print("Go to http://127.0.0.1:5050/ for further configuration setup.")
        subprocess.Popen(["python3", os.path.abspath(__file__), "--background"],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
        host_ip = get_eth0_ip()
        sys.exit(0)
    else:
        log("Web config server starting silently in background")
        log("Web config server now running on http://127.0.0.1:5050")
        import socket
def get_eth0_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        log(f"Failed to detect eth0 IP: {e}")
        return "127.0.0.1"

host_ip = get_eth0_ip()
log(f"Web config server now running on http://{host_ip}:5050")
app.run(host=host_ip, port=5050, debug=False)