import xml.etree.ElementTree as ET
from .base_collector import BaseCollector

class InterfaceCounterCollector(BaseCollector):
    """
    Collector for interface counter metrics from PAN-OS.
    Parses <show><counter><interface>all</interface></counter></show> XML.
    """
    def __init__(self):
        super().__init__(
            name="interface_counter_collector",
            api_command="<show><counter><interface>all</interface></counter></show>",
            help_text="Interface counter metrics from PAN-OS"
        )

    def parse(self, xml_data, device_config):
        """
        Parse interface counter XML and emit Prometheus metrics.
        """
        metrics = []
        try:
            root = ET.fromstring(xml_data)
            device = device_config['host']
            # Parse <hw>/entry
            for entry in root.findall('.//hw/entry'):
                iface = entry.findtext('name') or entry.findtext('interface')
                if not iface:
                    continue
                # Top-level numeric fields
                for child in entry:
                    if child.tag in ('name', 'interface', 'port'):
                        continue
                    try:
                        value = int(child.text)
                        tag = self.sanitize_metric_name(child.tag)
                        metrics.append(self.prometheus_metric(
                            metric=f"panos_interface_counter_{tag}",
                            value=value,
                            device=device,
                            help_text=f"Interface counter: {tag}",
                            labels={"interface": iface}
                        ))
                    except (ValueError, TypeError):
                        pass
                # <port> child: nested counters
                port = entry.find('port')
                if port is not None:
                    for pchild in port:
                        try:
                            value = int(pchild.text)
                            tag = self.sanitize_metric_name(pchild.tag)
                            metrics.append(self.prometheus_metric(
                                metric=f"panos_interface_counter_{tag}",
                                value=value,
                                device=device,
                                help_text=f"Interface port counter: {tag}",
                                labels={"interface": iface}
                            ))
                        except (ValueError, TypeError):
                            pass
            # Parse <ifnet>/ifnet/entry
            for entry in root.findall('.//ifnet/ifnet/entry'):
                iface = entry.findtext('name')
                if not iface:
                    continue
                for child in entry:
                    if child.tag == 'name':
                        continue
                    try:
                        value = int(child.text)
                        tag = self.sanitize_metric_name(child.tag)
                        metrics.append(self.prometheus_metric(
                            metric=f"panos_interface_counter_{tag}",
                            value=value,
                            device=device,
                            help_text=f"Interface ifnet counter: {tag}",
                            labels={"interface": iface}
                        ))
                    except (ValueError, TypeError):
                        pass
                    # <counters> child: nested counters
                    if child.tag == 'counters':
                        for cchild in child:
                            try:
                                value = int(cchild.text)
                                tag = self.sanitize_metric_name(cchild.tag)
                                metrics.append(self.prometheus_metric(
                                    metric=f"panos_interface_counter_{tag}",
                                    value=value,
                                    device=device,
                                    help_text=f"Interface ifnet counters: {tag}",
                                    labels={"interface": iface}
                                ))
                            except (ValueError, TypeError):
                                pass
        except Exception as e:
            return self.prometheus_error_metric(device_config['host'], f"interface_counter_parse: {e}")
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
