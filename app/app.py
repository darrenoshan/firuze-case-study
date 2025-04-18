#!/usr/bin/env python3

from flask import Flask
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
import prometheus_client
from flask import Response

app = Flask(__name__)

# === Metrics ===
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP Requests', ['method', 'endpoint'])

@app.before_request
def before_request():
    # Track every request
    from flask import request
    REQUEST_COUNT.labels(request.method, request.path).inc()

# === Routes ===
@app.route('/v1/health', methods=['GET'])
def health_check():
    return 'ok', 200

@app.route('/v1/ready', methods=['GET'])
def ready_check():
    return 'ready', 200

@app.route('/index.html', methods=['GET'])
def default():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>My Hello Page</title>
    </head>
    <body>
        <h1>Hello, World</h1>
    </body>
    </html>
    ''', 200

@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

if __name__ == '__main__':
    # Start default Prometheus metrics server on /metrics
    app.run(host='0.0.0.0', port=8080)
