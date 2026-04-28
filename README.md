# internal-observability-stack

Self-hosted observability stack for internal services on **TrueNAS SCALE**.

`internal-observability-stack` is a compact monitoring platform for containerized workloads, combining application metrics, infrastructure telemetry, database monitoring, synthetic endpoint checks and centralized alerting in a single Docker Compose deployment.

## Stack

- Flask service
- PostgreSQL
- Prometheus
- Grafana
- node-exporter
- postgres-exporter
- blackbox-exporter
- Matrix / Element webhook bridge

## Architecture

```text
application -> /metrics ---------------------> Prometheus
PostgreSQL -> postgres-exporter ------------> Prometheus
host       -> node-exporter ----------------> Prometheus
endpoints  -> blackbox-exporter -----------> Prometheus
Prometheus -> Grafana dashboards/alerts
Grafana    -> webhook bridge -> Matrix / Element
```

## Monitoring domains

### Service telemetry
- request throughput (RPS)
- 5xx error rate
- latency percentiles
- per-endpoint p95 latency

### Infrastructure telemetry
- CPU utilization
- memory usage
- network RX/TX

### Database telemetry
- active connections
- commits / rollbacks
- inserts
- database size

### Availability telemetry
- probe success / failure
- external probe latency
- HTTP status code visibility

## Deployment target

This stack is designed to run on **TrueNAS SCALE** using dataset-backed host paths and Docker Compose, which makes it useful for validating:

- mounted paths under `/mnt/...`
- permissions on host-mounted configs
- networking and port conflicts
- persistence for Grafana and PostgreSQL
- observability patterns for self-hosted infrastructure

## Run

From the project directory on TrueNAS SCALE:

```bash
sudo docker compose up -d --build
```

Default endpoints:

- App: `http://<TRUENAS_IP>:5000`
- Grafana: `http://<TRUENAS_IP>:3000`
- Prometheus: `http://<TRUENAS_IP>:9090`

## Project value

This repository is intended as a compact **reference observability environment** for internal services. It can be used to validate telemetry collection, dashboard design, alert rules and notification routing before scaling the same approach to a larger platform.
