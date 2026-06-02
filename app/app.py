from flask import Flask, jsonify, request
import socket
import datetime
import os
import pymysql

app = Flask(__name__)
hostname = socket.gethostname()

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "10.0.0.31"),
    "user": os.environ.get("DB_USER", "app_user"),
    "password": os.environ["DB_PASSWORD"],
    "database": os.environ.get("DB_NAME", "company_db"),
    "charset": "utf8mb4"
}


def get_db_connection():
    return pymysql.connect(**DB_CONFIG)


@app.route("/")
def index():
    return jsonify({
        "server": hostname,
        "status": "running",
        "timestamp": datetime.datetime.now().isoformat()
    })


@app.route("/health")
def health():
    return jsonify({
        "server": hostname,
        "status": "ok"
    })


@app.route("/db")
def db_check():
    try:
        conn = get_db_connection()

        with conn.cursor() as cur:
            cur.execute("SELECT 1")

        conn.close()

        return jsonify({
            "server": hostname,
            "db": "connection success"
        })

    except Exception as e:
        return jsonify({
            "server": hostname,
            "db": "connection failed",
            "error": str(e)
        }), 500


@app.route("/visit")
def visit():
    client_ip = request.headers.get("X-Real-IP", request.remote_addr)

    try:
        conn = get_db_connection()

        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO visits (app_name, client_ip) VALUES (%s, %s)",
                (hostname, client_ip)
            )

        conn.commit()
        conn.close()

        return jsonify({
            "server": hostname,
            "message": "visit recorded",
            "client_ip": client_ip
        })

    except Exception as e:
        return jsonify({
            "server": hostname,
            "error": str(e)
        }), 500


@app.route("/record")
def record():
    try:
        conn = get_db_connection()

        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute(
                "SELECT id, app_name, client_ip, created_at "
                "FROM visits "
                "ORDER BY id DESC "
                "LIMIT 10"
            )
            rows = cur.fetchall()

        conn.close()

        return jsonify({
            "server": hostname,
            "count": len(rows),
            "record": rows
        })

    except Exception as e:
        return jsonify({
            "server": hostname,
            "error": str(e)
        }), 500


@app.route("/info")
def info():
    return jsonify({
        "server": hostname,
        "host": request.headers.get("Host"),
        "x_real_ip": request.headers.get("X-Real-IP"),
        "x_forwarded_for": request.headers.get("X-Forwarded-For"),
        "x_forwarded_proto": request.headers.get("X-Forwarded-Proto"),
        "remote_addr": request.remote_addr
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)