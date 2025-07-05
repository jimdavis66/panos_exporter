import requests
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
import logging
from requests.adapters import HTTPAdapter, Retry
import re

class BaseCollector(ABC):
    """
    Base class for PAN-OS collectors.
    - Handles XML API call with retries and error logging
    - Parses XML and emits Prometheus metrics
    - Subclasses must implement parse()
    """
    def __init__(self, name, api_command, help_text):
        self.name = name
        self.api_command = api_command
        self.help_text = help_text
        self.logger = logging.getLogger(f"panos_exporter.{self.name}")
        # Set up a session with retries
        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

    def collect(self, device_config):
        """
        Calls the PAN-OS XML API with retries and returns parsed metrics.
        Logs errors and emits Prometheus error metrics on failure.
        """
        url = f"https://{device_config['host']}/api/"
        params = {
            'type': 'op',
            'cmd': self.api_command,
            'key': device_config.get('api_key'),
        }
        try:
            response = self.session.get(url, params=params, verify=False, timeout=5, auth=(device_config['username'], device_config['password']))
            response.raise_for_status()
            return self.parse(response.text, device_config)
        except Exception as e:
            self.logger.error(f"HTTP error for device={device_config['host']}: {e}")
            return self.prometheus_error_metric(device_config['host'], str(e))

    @abstractmethod
    def parse(self, xml_data, device_config):
        """
        Parse XML and return Prometheus-formatted metrics as a string.
        """
        pass

    def prometheus_metric(self, metric, value, device, metric_type='gauge', help_text=None, labels=None):
        """
        Format a Prometheus metric line with HELP/TYPE and labels. Do not emit an 'instance' or 'device' label.
        """
        help_text = help_text or self.help_text
        if labels:
            label_str = '{' + ','.join(f'{k}="{v}"' for k, v in labels.items()) + '}'
        else:
            label_str = ''
        return f"# HELP {metric} {help_text}\n# TYPE {metric} {metric_type}\n{metric}{label_str} {value}\n"

    def prometheus_error_metric(self, device, error):
        """
        Emit a Prometheus error metric for a failed scrape. Do not emit an 'instance' or 'device' label.
        """
        return f"# HELP panos_error Error metric\n# TYPE panos_error gauge\npanos_error{{error=\"{error}\"}} 1\n"

    @staticmethod
    def sanitize_metric_name(name):
        """
        Sanitize a metric name to match Prometheus regex [a-zA-Z_:][a-zA-Z0-9_:]* by replacing any character not in [a-zA-Z0-9_] with an underscore.
        """
        return re.sub(r'[^a-zA-Z0-9_]', '_', name)
