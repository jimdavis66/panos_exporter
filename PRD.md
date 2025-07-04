# **Product Requirements Document: panos\_exporter**

## Overview

**panos\_exporter** is a Prometheus exporter written in Python using the Flask framework. It retrieves operational and performance metrics from Palo Alto firewalls via the XML-API and exposes them in Prometheus format. The tool is inspired by [jenningsloy318/panos\_exporter](https://github.com/jenningsloy318/panos_exporter) but with a stronger focus on metric coverage, Prometheus output compliance, and configurability.

---

## Goals

* Query multiple Palo Alto PAN-OS devices using XML-API
* Collect metrics from 7 key diagnostic API endpoints
* Serve metrics on an HTTP endpoint in Prometheus exposition format
* Comply with Prometheus metric standards (with `# HELP` and `# TYPE` lines)
* Use YAML-based configuration for device IPs and credentials
* Run as a Docker container

---

## Non-Goals

* SNMP or CLI-based metric collection
* Configuration via GUI or CLI flags
* Support for non-PAN-OS devices

---

## Architecture

### Components

* **Flask App**: Serves `/metrics` endpoint
* **Collectors**: Python classes for each PAN-OS XML-API endpoint
* **Configuration Loader**: Parses YAML file with device targets and credentials
* **Exporter Engine**: Calls collectors, parses XML, and emits metrics
* **Docker Container**: Production containerization using a `Dockerfile`

---

## API Endpoints to Query

| Collector Name                                    | XML API Command                                                                                        |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| system\_info\_collector                           | `<show><system><info></info></system></show>`                                                          |
| system\_environmentals\_collector                 | `<show><system><environmentals></environmentals></system></show>`                                      |
| global\_counter\_collector                        | `<show><counter><global></global></counter></show>`                                                    |
| session\_collector                                | `<show><session><info></info></session></show>`                                                        |
| interface\_collector                              | `<show><interface>all</interface></show>`                                                              |
| interface\_counter\_collector                     | `<show><counter><interface>all</interface></counter></show>`                                           |
| data\_processor\_resource\_utilization\_collector | `<show><running><resource-monitor><second><last>1</last></second></resource-monitor></running></show>` |

Each collector should:

* Retrieve XML via HTTPS GET
* Parse data using `xml.etree.ElementTree`
* Extract metrics and emit Prometheus-compliant lines

---

## Example Prometheus Output Format

For each metric, output:

```text
# HELP panos_global_counter_ctd_dns_action_block global counter for DNS signature trigger block action
# TYPE panos_global_counter_ctd_dns_action_block gauge
panos_global_counter_ctd_dns_action_block{device="10.36.48.15"} 42
```

---

## Configuration

### YAML Configuration File

`config.yaml`:

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

The exporter must support multiple devices and poll each when `/metrics` is hit. Authentication uses basic auth with POST (if required).

---

## Prometheus Configuration

```yaml
- job_name: 'panos_exporter'
  metrics_path: /metrics
  static_configs:
  - targets:
    - 192.168.1.15
  relabel_configs:
    - source_labels: [__address__]
      target_label: __param_target
    - source_labels: [__param_target]
      target_label: instance
    - target_label: __address__
      replacement: panos_exporter:9654
```

---

## Flask App

### Endpoint

* `/metrics`: Accepts `target` query param (e.g., `?target=192.168.1.15`)
* Returns:

  * `200 OK` with Prometheus-formatted metrics
  * `400 Bad Request` if device not configured

---

## Directory Structure

```
panos_exporter/
├── app/
│   ├── __init__.py
│   ├── app.py                    # Flask entry point
│   ├── config_loader.py          # YAML config loader
│   ├── exporter.py               # Core exporter logic
│   └── collectors/               # Collector modules for each API command
│       ├── __init__.py
│       ├── base_collector.py
│       ├── system_info_collector.py
│       ├── system_environmentals_collector.py
│       ├── global_counter_collector.py
│       ├── session_collector.py
│       ├── interface_collector.py
│       ├── interface_counter_collector.py
│       └── data_processor_resource_utilization_collector.py
├── config.yaml                   # Device credentials
├── requirements.txt              # Python dependencies
└── Dockerfile                    # Container definition
```

---

## Error Handling

* Log XML parsing errors with `device`, `collector`, and `timestamp`
* Return partial metrics if one collector fails
* Timeout HTTP calls after 5 seconds
* Support debug logging via environment variable

---

## 🧭 **Project Milestones for `panos_exporter`**

### ✅ **Milestone 1: Project Setup & Configuration**

**Goal:** Lay the foundational structure of the project.

* [x] Create the updated directory structure
* [x] Scaffold `app/` module and subfolders
* [x] Create placeholder/stub collectors in `collectors/`
* [x] Add `__init__.py` to enable modular imports
* [x] Create `requirements.txt`
* [x] Write `Dockerfile` with Flask runtime

✅ **Outcome**: Project runs a basic Flask app and loads configuration from `config.yaml`.

---

### 🚀 **Milestone 2: Flask Metrics Endpoint**

**Goal:** Expose a working `/metrics` endpoint for Prometheus to scrape.

* [x] Build `app.py` with Flask, handle `?target=` query parameter
* [x] Validate target exists in config
* [x] Return a simple Prometheus-formatted metric as a stub
* [x] Add error handling for unknown targets
* [x] Expose app on port 9654

✅ **Outcome**: Prometheus can scrape `http://<host>:9654/metrics?target=...` and receive valid output.

---

### 🔌 **Milestone 3: Implement Core Collector Framework**

**Goal:** Enable modular collectors and unified metric output.

* [x] Create `base_collector.py` with interface methods
* [x] Implement XML API call logic using `requests`
* [x] Parse XML with `ElementTree`
* [x] Support Prometheus metric format: `# HELP`, `# TYPE`, `metric{labels} value`

✅ **Outcome**: Base collector works with real PAN-OS XML API responses and emits valid metrics.

---

### 📊 **Milestone 4: Implement All 7 Collectors**

**Goal:** Collect and emit real metrics from PAN-OS.

* [x] `system_info_collector.py`
* [x] `system_environmentals_collector.py`
* [x] `global_counter_collector.py`
* [x] `session_collector.py`
* [x] `interface_collector.py`
* [x] `interface_counter_collector.py`
* [x] `data_processor_resource_utilization_collector.py`

✅ **Outcome**: Each collector parses real XML from the firewall and emits one or more `gauge` metrics per spec.

---

### 🐳 **Milestone 5: Containerization and Prometheus Integration**

**Goal:** Run and scrape the exporter from Prometheus in Docker.

* [x] Build and run the Docker container
* [x] Confirm `/metrics` endpoint works in container
* [x] Add sample `prometheus.yml` for integration testing
* [x] Test relabeling with multiple devices
* [x] Allow the user to choose which collectors run via the `config.yml` file

✅ **Outcome**: Prometheus scrapes containerized exporter and gets real metrics.

---

### 🔐 **Milestone 6: Stability, Logging & Error Handling**

**Goal:** Make the exporter production-ready.

* [ ] Add timeouts and retries to all HTTP calls
* [ ] Add logging for device/collector errors
* [ ] Ensure partial failures don't break endpoint
* [ ] Add debug mode via environment variable
* [ ] Validate YAML schema (e.g., IP, username, password presence)
* [ ] Ensure all standard Prometheus metrics are included, such as 'up'

✅ **Outcome**: Exporter is resilient, logs errors clearly, and doesn't crash on partial failures.

---

### 📦 **Milestone 7 (Optional): Polish and Extend**

**Goal:** Improve maintainability and prep for open-source release or team adoption.

* [ ] Add README.md with usage, config, and Prometheus setup
* [ ] Add comments/docstrings for maintainability
* [ ] Add unit tests for core modules (config, XML parsing)
* [ ] Optional: support TLS for the exporter's HTTP server

✅ **Outcome**: Exporter is documented, maintainable, and optionally secure.

---
