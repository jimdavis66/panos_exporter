from app.collectors.base_collector import BaseCollector
from app.collectors.system_info_collector import SystemInfoCollector
from app.collectors.system_environmentals_collector import SystemEnvironmentalsCollector
from app.collectors.global_counter_collector import GlobalCounterCollector
from app.collectors.session_collector import SessionCollector
from app.collectors.interface_collector import InterfaceCollector
from app.collectors.interface_counter_collector import InterfaceCounterCollector
from app.collectors.data_processor_resource_utilization_collector import DataProcessorResourceUtilizationCollector

COLLECTOR_CLASS_MAP = {
    'system_info_collector': SystemInfoCollector,
    'system_environmentals_collector': SystemEnvironmentalsCollector,
    'global_counter_collector': GlobalCounterCollector,
    'session_collector': SessionCollector,
    'interface_collector': InterfaceCollector,
    'interface_counter_collector': InterfaceCounterCollector,
    'data_processor_resource_utilization_collector': DataProcessorResourceUtilizationCollector,
}

class Exporter:
    """
    Aggregates all enabled collectors and exposes unified Prometheus metrics for a device.
    Emits a panos_up metric (1=all collectors succeed, 0=any fail).
    """
    def __init__(self, config):
        self.config = config
        collector_names = config.get('collectors')
        if collector_names:
            self.collectors = []
            for name in collector_names:
                cls = COLLECTOR_CLASS_MAP.get(name)
                if cls:
                    self.collectors.append(cls())
        else:
            # fallback: load all collectors
            self.collectors = [
                SystemInfoCollector(),
                SystemEnvironmentalsCollector(),
                GlobalCounterCollector(),
                SessionCollector(),
                InterfaceCollector(),
                InterfaceCounterCollector(),
                DataProcessorResourceUtilizationCollector()
            ]

    def collect_metrics(self, target):
        """
        Collect metrics from all enabled collectors for the given device.
        Returns Prometheus-formatted string with up/error metrics.
        """
        device_config = self.config['devices'][target].copy()
        device_config['host'] = target
        output = ''
        up = 1
        error_metrics = []
        for collector in self.collectors:
            try:
                result = collector.collect(device_config)
                # If error metric present, mark up=0
                if '# TYPE panos_error gauge' in result:
                    up = 0
                    error_metrics.append(result)
                else:
                    output += result
            except Exception as e:
                up = 0
                error_msg = f"collector_failed: {collector.name}: {e}"
                error_metrics.append(f"# HELP panos_error Error metric\n# TYPE panos_error gauge\npanos_error{{device=\"{target}\",error=\"{error_msg}\"}} 1\n")
        # Emit up metric first
        up_metric = f"# HELP panos_up Device scrape status (1=up, 0=error)\n# TYPE panos_up gauge\npanos_up{{device=\"{target}\"}} {up}\n"
        return up_metric + ''.join(error_metrics) + output
