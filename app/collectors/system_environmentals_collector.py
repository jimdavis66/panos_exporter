from .base_collector import BaseCollector
import xml.etree.ElementTree as ET

class SystemEnvironmentalsCollector(BaseCollector):
    """
    Collector for system environmentals metrics from PAN-OS.
    Parses <show><system><environmentals></environmentals></system></show> XML.
    """
    def __init__(self):
        super().__init__(
            name="system_environmentals_collector",
            api_command="<show><system><environmentals></environmentals></system></show>",
            help_text="System environmentals metrics from PAN-OS"
        )

    def parse(self, xml_data, device_config):
        """
        Parse system environmentals XML and emit Prometheus metrics.
        """
        metrics = []
        try:
            root = ET.fromstring(xml_data)
            device = device_config['host']
            # Thermal sensors
            for entry in root.findall('.//thermal//entry'):
                desc = entry.findtext('description', default='unknown')
                temp = entry.findtext('DegreesC')
                alarm = entry.findtext('alarm', default='False').lower() == 'true'
                if temp is not None:
                    metrics.append(self.prometheus_metric(
                        metric="panos_thermal_sensor_celsius",
                        value=temp,
                        device=device,
                        help_text="Thermal sensor temperature in Celsius",
                        labels={"sensor": desc, "alarm": str(alarm).lower()}
                    ))
            # Fan sensors
            for entry in root.findall('.//fan//entry'):
                desc = entry.findtext('description', default='unknown')
                rpm = entry.findtext('RPMs')
                alarm = entry.findtext('alarm', default='False').lower() == 'true'
                if rpm is not None:
                    metrics.append(self.prometheus_metric(
                        metric="panos_fan_rpm",
                        value=rpm,
                        device=device,
                        help_text="Fan speed in RPM",
                        labels={"fan": desc, "alarm": str(alarm).lower()}
                    ))
            # Power sensors (voltage) with deduplication
            seen_power_sensors = set()
            for entry in root.findall('.//power//entry'):
                desc = entry.findtext('description', default='unknown')
                volts = entry.findtext('Volts')
                alarm = entry.findtext('alarm', default='False').lower() == 'true'
                key = (desc, str(alarm).lower())
                if volts is not None and key not in seen_power_sensors:
                    metrics.append(self.prometheus_metric(
                        metric="panos_power_sensor_volts",
                        value=volts,
                        device=device,
                        help_text="Power sensor voltage in Volts",
                        labels={"sensor": desc, "alarm": str(alarm).lower()}
                    ))
                    seen_power_sensors.add(key)
            # Power supply status
            for entry in root.findall('.//power-supply//entry'):
                desc = entry.findtext('description', default='unknown')
                inserted = entry.findtext('Inserted', default='False').lower() == 'true'
                alarm = entry.findtext('alarm', default='False').lower() == 'true'
                metrics.append(self.prometheus_metric(
                    metric="panos_power_supply_inserted",
                    value=int(inserted),
                    device=device,
                    help_text="Power supply inserted (1=True, 0=False)",
                    labels={"supply": desc, "alarm": str(alarm).lower()}
                ))
        except Exception as e:
            return self.prometheus_error_metric(device_config['host'], f"system_environmentals_parse: {e}")
        return ''.join(metrics)
