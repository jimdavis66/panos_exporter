from .base_collector import BaseCollector
import xml.etree.ElementTree as ET

class SessionCollector(BaseCollector):
    """
    Collector for session info metrics from PAN-OS.
    Parses <show><session><info></info></session></show> XML.
    """
    def __init__(self):
        super().__init__(
            name="session_collector",
            api_command="<show><session><info></info></session></show>",
            help_text="Session info metrics from PAN-OS"
        )

    def parse(self, xml_data, device_config):
        """
        Parse session info XML and emit Prometheus metrics.
        """
        metrics = []
        try:
            root = ET.fromstring(xml_data)
            device = device_config['host']
            result = root.find('.//result')
            if result is not None:
                for elem in result:
                    tag = elem.tag.replace('-', '_')
                    value = elem.text
                    # Try to parse as int or float
                    try:
                        num_value = int(value)
                        metrics.append(self.prometheus_metric(
                            metric=f"panos_session_{tag}",
                            value=num_value,
                            device=device,
                            help_text=f"Session info: {tag}"
                        ))
                        continue
                    except (ValueError, TypeError):
                        try:
                            num_value = float(value)
                            metrics.append(self.prometheus_metric(
                                metric=f"panos_session_{tag}",
                                value=num_value,
                                device=device,
                                help_text=f"Session info: {tag}"
                            ))
                            continue
                        except (ValueError, TypeError):
                            pass
                    # Boolean
                    if value in ('True', 'False'):
                        metrics.append(self.prometheus_metric(
                            metric=f"panos_session_{tag}",
                            value=1 if value == 'True' else 0,
                            device=device,
                            help_text=f"Session info: {tag} (1=True, 0=False)"
                        ))
                        continue
                    # String: emit as info metric with label
                    metrics.append(self.prometheus_metric(
                        metric=f"panos_session_{tag}_info",
                        value=1,
                        device=device,
                        help_text=f"Session info: {tag} (info label)",
                        labels={"value": value}
                    ))
        except Exception as e:
            return self.prometheus_error_metric(device_config['host'], f"session_info_parse: {e}")
        # Deduplicate metrics
        seen = set()
        deduped_metrics = []
        for m in metrics:
            lines = m.split('\n')
            metric_line = next((l for l in lines if l and not l.startswith('#')), None)
            if metric_line:
                metric_name = metric_line.split('{')[0]
                label_str = metric_line.split('{')[1].split('}')[0] if '{' in metric_line else ''
                key = (metric_name, label_str)
                if key not in seen:
                    seen.add(key)
                    deduped_metrics.append(m)
        return ''.join(deduped_metrics)
