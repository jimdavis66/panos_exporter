import xml.etree.ElementTree as ET

from .base_collector import BaseCollector
from .routing_helpers import dedupe_metrics, parse_route_category_metrics


class RoutingResourceCollector(BaseCollector):
    """
    Collector for routing resource metrics from PAN-OS.
    Parses <show><routing><resource></resource></routing></show> XML.
    """

    def __init__(self):
        super().__init__(
            name="routing_resource_collector",
            api_command="<show><routing><resource></resource></routing></show>",
            help_text="Routing resource utilization metrics from PAN-OS",
        )

    def parse(self, xml_data, device_config):
        metrics = []
        try:
            root = ET.fromstring(xml_data)
            device = device_config["host"]
            entry = root.find(".//result/entry")
            if entry is not None:
                metrics.extend(
                    parse_route_category_metrics(
                        entry,
                        "panos_routing_resource",
                        device,
                        self.prometheus_metric,
                    )
                )
        except Exception as e:
            return self.prometheus_error_metric(
                device_config["host"], f"routing_resource_parse: {e}"
            )
        return "".join(dedupe_metrics(metrics))
