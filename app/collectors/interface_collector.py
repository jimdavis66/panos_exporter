import xml.etree.ElementTree as ET
from .base_collector import BaseCollector

class InterfaceCollector(BaseCollector):
    """
    Collector for interface metrics from PAN-OS.
    Parses <show><interface>all</interface></show> XML.
    """
    def __init__(self):
        super().__init__(
            name="interface_collector",
            api_command="<show><interface>all</interface></show>",
            help_text="Interface metrics from PAN-OS"
        )

    def parse(self, xml_data, device_config):
        """
        Parse interface XML and emit Prometheus metrics.
        """
        metrics = []
        try:
            root = ET.fromstring(xml_data)
            device = device_config['host']
            # Parse <hw> section for physical interface info
            hw_info = {}
            for entry in root.findall('.//hw/entry'):
                name = entry.findtext('name')
                if not name:
                    continue
                hw_info[name] = {
                    'mac': entry.findtext('mac', default='unknown'),
                    'speed': entry.findtext('speed', default='ukn'),
                    'duplex': entry.findtext('duplex', default='ukn'),
                    'state': entry.findtext('state', default='unknown'),
                    'type': entry.findtext('type', default='unknown'),
                }
            # Parse <ifnet> section for logical interface info
            for entry in root.findall('.//ifnet/entry'):
                name = entry.findtext('name')
                if not name:
                    continue
                # Merge with hw info if available
                hw = hw_info.get(name, {})
                mac = hw.get('mac', 'unknown')
                speed = hw.get('speed', 'ukn')
                duplex = hw.get('duplex', 'ukn')
                state = hw.get('state', 'unknown')
                type_code = hw.get('type', 'unknown')
                # Map type code to string if possible
                type_map = {
                    '0': 'ethernet',
                    '2': 'ha',
                    '3': 'vlan',
                    '4': 'aggregate',
                    '5': 'loopback',
                    '6': 'tunnel',
                    '7': 'hsci',
                }
                type_str = type_map.get(str(type_code), str(type_code))
                # Logical info
                zone = entry.findtext('zone', default='')
                vsys = entry.findtext('vsys', default='')
                tag = entry.findtext('tag', default='')
                fwd = entry.findtext('fwd', default='')
                ip = entry.findtext('ip', default='')
                # State metric (1=up, 0=down, -1=unknown)
                state_val = 1 if state.lower() == 'up' else (0 if state.lower() == 'down' else -1)
                metrics.append(self.prometheus_metric(
                    metric="panos_interface_state",
                    value=state_val,
                    device=device,
                    help_text="Interface state (1=up, 0=down, -1=unknown)",
                    labels={
                        "interface": name,
                        "mac": mac,
                        "type": type_str,
                        "zone": zone,
                        "vsys": vsys,
                        "tag": tag,
                        "fwd": fwd,
                        "ip": ip
                    }
                ))
                # Speed metric (emit only if numeric)
                try:
                    speed_val = int(speed)
                    metrics.append(self.prometheus_metric(
                        metric="panos_interface_speed",
                        value=speed_val,
                        device=device,
                        help_text="Interface speed (Mbps)",
                        labels={"interface": name}
                    ))
                except (ValueError, TypeError):
                    pass
                # Duplex metric (1=full, 0=half, -1=unknown)
                duplex_val = 1 if duplex.lower() == 'full' else (0 if duplex.lower() == 'half' else -1)
                metrics.append(self.prometheus_metric(
                    metric="panos_interface_duplex",
                    value=duplex_val,
                    device=device,
                    help_text="Interface duplex (1=full, 0=half, -1=unknown)",
                    labels={"interface": name}
                ))
            # Optionally, emit metrics for interfaces in <hw> but not in <ifnet>
            for name, hw in hw_info.items():
                if name in [e.findtext('name') for e in root.findall('.//ifnet/entry')]:
                    continue
                mac = hw.get('mac', 'unknown')
                speed = hw.get('speed', 'ukn')
                duplex = hw.get('duplex', 'ukn')
                state = hw.get('state', 'unknown')
                type_code = hw.get('type', 'unknown')
                type_map = {
                    '0': 'ethernet',
                    '2': 'ha',
                    '3': 'vlan',
                    '4': 'aggregate',
                    '5': 'loopback',
                    '6': 'tunnel',
                    '7': 'hsci',
                }
                type_str = type_map.get(str(type_code), str(type_code))
                state_val = 1 if state.lower() == 'up' else (0 if state.lower() == 'down' else -1)
                metrics.append(self.prometheus_metric(
                    metric="panos_interface_state",
                    value=state_val,
                    device=device,
                    help_text="Interface state (1=up, 0=down, -1=unknown)",
                    labels={
                        "interface": name,
                        "mac": mac,
                        "type": type_str
                    }
                ))
                try:
                    speed_val = int(speed)
                    metrics.append(self.prometheus_metric(
                        metric="panos_interface_speed",
                        value=speed_val,
                        device=device,
                        help_text="Interface speed (Mbps)",
                        labels={"interface": name}
                    ))
                except (ValueError, TypeError):
                    pass
                duplex_val = 1 if duplex.lower() == 'full' else (0 if duplex.lower() == 'half' else -1)
                metrics.append(self.prometheus_metric(
                    metric="panos_interface_duplex",
                    value=duplex_val,
                    device=device,
                    help_text="Interface duplex (1=full, 0=half, -1=unknown)",
                    labels={"interface": name}
                ))
        except Exception as e:
            return self.prometheus_error_metric(device_config['host'], f"interface_parse: {e}")
        return ''.join(metrics)
