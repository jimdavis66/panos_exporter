from .base_collector import BaseCollector
import xml.etree.ElementTree as ET

class GlobalCounterCollector(BaseCollector):
    """
    Collector for global counter metrics from PAN-OS.
    Parses <show><counter><global></global></counter></show> XML.
    """
    def __init__(self):
        super().__init__(
            name="global_counter_collector",
            api_command="<show><counter><global></global></counter></show>",
            help_text="Global counter metrics from PAN-OS"
        )

    def parse(self, xml_data, device_config):
        """
        Parse global counter XML and emit Prometheus metrics.
        """
        metrics = []
        try:
            root = ET.fromstring(xml_data)
            device = device_config['host']
            for entry in root.findall('.//global//counters//entry'):
                name = entry.findtext('name', default='unknown')
                value = entry.findtext('value')
                rate = entry.findtext('rate')
                severity = entry.findtext('severity', default='unknown')
                category = entry.findtext('category', default='unknown')
                aspect = entry.findtext('aspect', default='unknown')
                desc = entry.findtext('desc', default='')
                # Main value metric
                if value is not None:
                    metrics.append(self.prometheus_metric(
                        metric=f"panos_global_counter_{name}",
                        value=value,
                        device=device,
                        help_text=desc or f"Global counter for {name}",
                        labels={
                            "severity": severity,
                            "category": category,
                            "aspect": aspect
                        }
                    ))
                # Rate metric
                if rate is not None:
                    metrics.append(self.prometheus_metric(
                        metric=f"panos_global_counter_{name}_rate",
                        value=rate,
                        device=device,
                        help_text=f"Rate for {desc or name}",
                        labels={
                            "severity": severity,
                            "category": category,
                            "aspect": aspect
                        }
                    ))
        except Exception as e:
            return self.prometheus_error_metric(device_config['host'], f"global_counter_parse: {e}")
        return ''.join(metrics)
