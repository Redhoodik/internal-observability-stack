from flask import Flask, jsonify, Response, request
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time
import random
import psycopg2
import os

app = Flask(__name__)

REQUEST_COUNT = Counter(
    "app_http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "http_status"]
)

REQUEST_LATENCY = Histogram(
    "app_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"]
)


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "monitoring_lab"),
        user=os.getenv("DB_USER", "monitoring_user"),
        password=os.getenv("DB_PASSWORD", "monitoring_password"),
    )


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS visits (
            id SERIAL PRIMARY KEY,
            endpoint TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """
    )

    conn.commit()
    cur.close()
    conn.close()


@app.before_request
def before_request():
    request.start_time = time.time()


@app.after_request
def after_request(response):
    request_latency = time.time() - request.start_time

    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.path,
        http_status=response.status_code,
    ).inc()

    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.path,
    ).observe(request_latency)

    return response


@app.route("/")
def index():
    return jsonify({
        "status": "ok",
        "message": "service is running",
    })


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
    })


@app.route("/slow")
def slow():
    time.sleep(2)

    return jsonify({
        "status": "ok",
        "message": "response completed",
    })


@app.route("/error")
def error():
    if random.random() < 0.5:
        return jsonify({
            "status": "error",
            "message": "internal processing error",
        }), 500

    return jsonify({
        "status": "ok",
        "message": "request processed successfully",
    })


@app.route("/metrics")
def metrics():
    return Response(
        generate_latest(),
        mimetype=CONTENT_TYPE_LATEST,
    )


@app.route("/visit")
def visit():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO visits (endpoint) VALUES (%s);",
        ("/visit",),
    )

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({
        "status": "ok",
        "message": "event recorded successfully",
    })


@app.route("/visits")
def visits():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, endpoint, created_at FROM visits ORDER BY id DESC LIMIT 10;"
    )
    rows = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify([
        {
            "id": row[0],
            "endpoint": row[1],
            "created_at": row[2].isoformat(),
        }
        for row in rows
    ])


if __name__ == "__main__":
    init_db()
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
    )
