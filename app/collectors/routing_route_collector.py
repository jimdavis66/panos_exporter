import xml.etree.ElementTree as ET

from .base_collector import BaseCollector
from .routing_helpers import dedupe_metrics


class RoutingRouteCollector(BaseCollector):
    """
    Collector for routing table metrics from PAN-OS.
    Parses <show><routing><route><virtual-router>VR</virtual-router></route></routing></show> XML.
    """

    def __init__(self):
        super().__init__(
            name="routing_route_collector",
            api_command="",
            help_text="Routing table metrics from PAN-OS",
        )

    def _api_command(self, device_config):
        vr = device_config.get("virtual_router", "default")
        return (
            f"<show><routing><route><virtual-router>{vr}</virtual-router></route></routing></show>"
        )

    def collect(self, device_config):
        self.api_command = self._api_command(device_config)
        return super().collect(device_config)

    def parse(self, xml_data, device_config):
        metrics = []
        try:
            root = ET.fromstring(xml_data)
            device = device_config["host"]
            for entry in root.findall(".//result/entry"):
                labels = {
                    "virtual_router": entry.findtext("virtual-router", default="unknown"),
                    "destination": entry.findtext("destination", default="unknown"),
                    "nexthop": entry.findtext("nexthop", default=""),
                    "interface": entry.findtext("interface", default=""),
                    "route_table": entry.findtext("route-table", default="unknown"),
                    "flags": (entry.findtext("flags", default="") or "").strip(),
                }
                metrics.append(
                    self.prometheus_metric(
                        metric="panos_routing_route_info",
                        value=1,
                        device=device,
                        help_text="Active routing table entry",
                        labels=labels,
                    )
                )
                metric_text = (entry.findtext("metric") or "").strip()
                if metric_text:
                    try:
                        metrics.append(
                            self.prometheus_metric(
                                metric="panos_routing_route_metric",
                                value=int(metric_text),
                                device=device,
                                help_text="Routing table entry metric",
                                labels=labels,
                            )
                        )
                    except ValueError:
                        pass
                age_text = (entry.findtext("age") or "").strip()
                if age_text:
                    try:
                        metrics.append(
                            self.prometheus_metric(
                                metric="panos_routing_route_age_seconds",
                                value=int(age_text),
                                device=device,
                                help_text="Routing table entry age in seconds",
                                labels=labels,
                            )
                        )
                    except ValueError:
                        pass
        except Exception as e:
            return self.prometheus_error_metric(device_config["host"], f"routing_route_parse: {e}")
        return "".join(dedupe_metrics(metrics))
