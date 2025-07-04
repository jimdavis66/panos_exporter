from .base_collector import BaseCollector
import xml.etree.ElementTree as ET

class SystemInfoCollector(BaseCollector):
    """
    Collector for system info metrics from PAN-OS.
    Parses <show><system><info></info></system></show> XML.
    """
    def __init__(self):
        super().__init__(
            name="system_info_collector",
            api_command="<show><system><info></info></system></show>",
            help_text="System info metrics from PAN-OS"
        )

    def parse(self, xml_data, device_config):
        """
        Parse system info XML and emit Prometheus metrics.
        """
        metrics = []
        try:
            root = ET.fromstring(xml_data)
            system = root.find('.//system')
            device = device_config['host']
            if system is not None:
                # Uptime (convert to seconds if possible)
                uptime_str = system.findtext('uptime', default='0')
                uptime_seconds = self._parse_uptime(uptime_str)
                metrics.append(self.prometheus_metric(
                    metric="panos_system_uptime_seconds",
                    value=uptime_seconds,
                    device=device,
                    help_text="System uptime in seconds"
                ))
                # Software version
                sw_version = system.findtext('sw-version', default='unknown')
                metrics.append(self.prometheus_metric(
                    metric="panos_system_software_version_info",
                    value=1,
                    device=device,
                    help_text="System software version (info label)",
                    labels={"version": sw_version}
                ))
                # Model
                model = system.findtext('model', default='unknown')
                metrics.append(self.prometheus_metric(
                    metric="panos_system_model_info",
                    value=1,
                    device=device,
                    help_text="System model (info label)",
                    labels={"model": model}
                ))
                # Serial
                serial = system.findtext('serial', default='unknown')
                metrics.append(self.prometheus_metric(
                    metric="panos_system_serial_info",
                    value=1,
                    device=device,
                    help_text="System serial (info label)",
                    labels={"serial": serial}
                ))
                # Multi-vsys
                multi_vsys = 1 if system.findtext('multi-vsys', default='off').lower() == 'on' else 0
                metrics.append(self.prometheus_metric(
                    metric="panos_system_multi_vsys_enabled",
                    value=multi_vsys,
                    device=device,
                    help_text="System multi-vsys enabled (1=on, 0=off)"
                ))
                # Operational mode
                op_mode = system.findtext('operational-mode', default='unknown')
                metrics.append(self.prometheus_metric(
                    metric="panos_system_operational_mode_info",
                    value=1,
                    device=device,
                    help_text="System operational mode (info label)",
                    labels={"mode": op_mode}
                ))
                # Device certificate status
                cert_status = system.findtext('device-certificate-status', default='unknown')
                metrics.append(self.prometheus_metric(
                    metric="panos_system_device_certificate_status_info",
                    value=1,
                    device=device,
                    help_text="Device certificate status (info label)",
                    labels={"status": cert_status}
                ))
                # MAC count
                mac_count = system.findtext('mac_count', default=None)
                if mac_count is not None:
                    metrics.append(self.prometheus_metric(
                        metric="panos_system_mac_count",
                        value=mac_count,
                        device=device,
                        help_text="System MAC address count"
                    ))
        except Exception as e:
            return self.prometheus_error_metric(device_config['host'], f"system_info_parse: {e}")
        # Deduplicate metrics
        seen = set()
        deduped_metrics = []
        for m in metrics:
            # Extract metric name and label set from the metric string
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

    def _parse_uptime(self, uptime_str):
        # Example: '0 days, 20:32:51'
        try:
            days_part, time_part = uptime_str.split(' days, ')
            days = int(days_part.strip())
            h, m, s = map(int, time_part.strip().split(':'))
            return days * 86400 + h * 3600 + m * 60 + s
        except Exception:
            return 0
