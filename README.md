# panos_exporter

A Prometheus exporter for Palo Alto PAN-OS firewalls, written in Python. It collects operational and performance metrics via the XML-API and exposes them in Prometheus format. This project is strongly influenced by [jenningsloy318/panos_exporter](https://github.com/jenningsloy318/panos_exporter) 

## Features
- Collects metrics from 11 PAN-OS diagnostic and routing endpoints
- Modular collector framework
- YAML-based device and collector configuration
- Production-ready Docker container
- Robust error handling and logging
- Dynamic collector selection
- Prometheus-compliant output

## Setup Options
Copy `config.yaml.example` to `config.yaml` and fill in device credentials. The image does not include this file; it is mounted at runtime.

Copy `.env.example` to `.env` to override listen port, Gunicorn settings, and debug logging. Compose reads `.env` automatically.

### 1. Run with Docker Compose
See `compose.yml` for a production example. From the repo root, with `config.yaml` in place:

```sh
docker compose up -d
```

### 1. Build and Run with Docker
Local builds pull Docker Hardened Images from `dhi.io`, so log in first:

```sh
docker login dhi.io
docker build -t panos_exporter .
docker run -p 9654:9654 -v $(pwd)/config.yaml:/app/config.yaml:ro panos_exporter
```

### Why `app/gunicorn_entrypoint.py` exists
This image is built on a minimal Python base that **does not include a shell** (no `sh`). That means we can’t reliably use a shell-form `CMD` like `sh -c "gunicorn ..."` to expand environment variables.

Instead, `app/gunicorn_entrypoint.py` reads runtime settings from environment variables (like `PORT`, worker/thread counts, timeouts) and then `exec()`s `gunicorn` directly, which is more robust in minimal containers and keeps configuration env-driven.

### 2. Local Development
```sh
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
ruff check app tests
ruff format --check app tests
pytest
export FLASK_ENV=development
python -m app.app
```

## Configuration
### config.yaml
```yaml
devices:
  192.168.1.15:
    username: user
    password: pass
    virtual_router: default
collectors:
  - system_info_collector
  - system_environmentals_collector
  - global_counter_collector
  - session_collector
  - interface_collector
  - interface_counter_collector
  - data_processor_resource_utilization_collector
  - routing_resource_collector
  - routing_summary_collector
  - routing_route_collector
  - routing_bgp_collector
```
- `devices`: Map of device IP/hostname to credentials
- `virtual_router`: Optional per-device setting used by `routing_route_collector` (defaults to `default`)
- `collectors`: List of collectors to run (omit for all)

Available collectors:
- `system_info_collector`
- `system_environmentals_collector`
- `global_counter_collector`
- `session_collector`
- `interface_collector`
- `interface_counter_collector`
- `data_processor_resource_utilization_collector`
- `routing_resource_collector`
- `routing_summary_collector`
- `routing_route_collector`
- `routing_bgp_collector`

## Prometheus Integration
### prometheus.yml
```yaml
scrape_configs:
  - job_name: 'panos_exporter'
    metrics_path: /metrics
    static_configs:
      - targets:
          - 192.168.1.15
          - 192.168.1.26
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: localhost:9654
```

## Usage
- Scrape: `http://<host>:9654/metrics?target=<device>`
- Only devices in `config.yaml` are allowed
- See logs for errors (set `DEBUG=1` for verbose output)

## Troubleshooting
- **No metrics?** Check logs for config or device errors
- **Collector errors?** See `panos_error` metrics and logs
- **Dynamic collector selection not working?** Ensure `collectors` list is correct in config
- **Config changes not picked up in Docker?** Use `-v $(pwd)/config.yaml:/app/config.yaml` to mount

## FAQ
- **Can I use hostnames instead of IPs?** Yes
- **How do I enable debug logging?** Set `DEBUG=1` in the environment
- **How do I add a new collector?** Add a Python class in `app/collectors/` and update the mapping in `exporter.py` 