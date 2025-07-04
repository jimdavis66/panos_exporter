import xml.etree.ElementTree as ET
from .base_collector import BaseCollector

class DataProcessorResourceUtilizationCollector(BaseCollector):
    """
    Collector for data processor resource utilization metrics from PAN-OS.
    Parses <show><running><resource-monitor><second><last>1</last></second></resource-monitor></running></show> XML.
    """
    def __init__(self):
        super().__init__(
            name="data_processor_resource_utilization_collector",
            api_command="<show><running><resource-monitor><second><last>1</last></second></resource-monitor></running></show>",
            help_text="Data processor resource utilization metrics from PAN-OS"
        )

    def parse(self, xml_data, device_config):
        """
        Parse data processor resource utilization XML and emit Prometheus metrics.
        """
        metrics = []
        try:
            root = ET.fromstring(xml_data)
            device = device_config['host']
            # Find all data processors (e.g., dp0, dp1, ...)
            for dp_elem in root.findall('.//data-processors/*'):
                dp_name = dp_elem.tag  # e.g., 'dp0'
                second = dp_elem.find('second')
                if second is None:
                    continue
                # <task> percent metrics
                task = second.find('task')
                if task is not None:
                    for tchild in task:
                        val = tchild.text
                        if val and val.endswith('%'):
                            try:
                                value = float(val.rstrip('%'))
                                metrics.append(self.prometheus_metric(
                                    metric=f"panos_data_processor_task_{tchild.tag}",
                                    value=value,
                                    device=device,
                                    help_text=f"Data processor {tchild.tag} utilization (%)",
                                    labels={"dp": dp_name}
                                ))
                            except ValueError:
                                pass
                # <cpu-load-average>/entry
                cpu_avg = second.find('cpu-load-average')
                if cpu_avg is not None:
                    for entry in cpu_avg.findall('entry'):
                        coreid = entry.findtext('coreid')
                        value = entry.findtext('value')
                        if coreid is not None and value is not None:
                            try:
                                metrics.append(self.prometheus_metric(
                                    metric="panos_data_processor_cpu_load_average",
                                    value=float(value),
                                    device=device,
                                    help_text="Data processor CPU load average per core",
                                    labels={"dp": dp_name, "coreid": coreid}
                                ))
                            except ValueError:
                                pass
                # <cpu-load-maximum>/entry
                cpu_max = second.find('cpu-load-maximum')
                if cpu_max is not None:
                    for entry in cpu_max.findall('entry'):
                        coreid = entry.findtext('coreid')
                        value = entry.findtext('value')
                        if coreid is not None and value is not None:
                            try:
                                metrics.append(self.prometheus_metric(
                                    metric="panos_data_processor_cpu_load_maximum",
                                    value=float(value),
                                    device=device,
                                    help_text="Data processor CPU load maximum per core",
                                    labels={"dp": dp_name, "coreid": coreid}
                                ))
                            except ValueError:
                                pass
                # <resource-utilization>/entry
                res_util = second.find('resource-utilization')
                if res_util is not None:
                    for entry in res_util.findall('entry'):
                        res_name = entry.findtext('name')
                        value = entry.findtext('value')
                        if res_name is not None and value is not None:
                            try:
                                metrics.append(self.prometheus_metric(
                                    metric="panos_data_processor_resource_utilization",
                                    value=float(value),
                                    device=device,
                                    help_text="Data processor resource utilization",
                                    labels={"dp": dp_name, "resource": res_name}
                                ))
                            except ValueError:
                                pass
        except Exception as e:
            return self.prometheus_error_metric(device_config['host'], f"data_processor_parse: {e}")
        return ''.join(metrics)
