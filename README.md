# panos_exporter

A Prometheus exporter for Palo Alto PAN-OS firewalls, written in Python. It collects operational and performance metrics via the XML-API and exposes them in Prometheus format. This project is strongly influenced by [jenningsloy318/panos_exporter](https://github.com/jenningsloy318/panos_exporter) 

## Features
- Collects metrics from 7 key PAN-OS diagnostic endpoints
- Modular collector framework
- YAML-based device and collector configuration
- Production-ready Docker container
- Robust error handling and logging
- Dynamic collector selection
- Prometheus-compliant output

## Setup Options
### 1. Run with Docker
```sh
docker run \
  -p 9654:9654 \
  -v $(pwd)/config.yaml:/app/config.yaml \
  ghcr.io/jimdavis66/panos_exporter
```

### 1. Build and Run with Docker
```sh
docker build -t panos_exporter .
docker run -p 9654:9654 -v $(pwd)/config.yaml:/app/config.yaml panos_exporter
```

### 2. Local Development
```sh
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export FLASK_ENV=development
python app/app.py
```

## Configuration
### config.yaml
```yaml
devices:
  192.168.1.15:
    username: user
    password: pass
collectors:
  - system_info_collector
  - system_environmentals_collector
  - global_counter_collector
  - session_collector
  - interface_collector
  - interface_counter_collector
  - data_processor_resource_utilization_collector
```
- `devices`: Map of device IP/hostname to credentials
- `collectors`: List of collectors to run (omit for all)

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