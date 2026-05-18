from flask import Flask, jsonify
import socket
import datetime

app = Flask(__name__)
hostname = socket.gethostname()


@app.route('/')
def index():
    return jsonify({
        "server": hostname,
        "status": "running",
        "timestamp": datetime.datetime.now().isoformat()
    })


@app.route('/health')
def health():
    return jsonify({
        "server": hostname,
        "status": "ok"
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)