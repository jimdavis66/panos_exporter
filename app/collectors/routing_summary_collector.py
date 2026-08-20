import xml.etree.ElementTree as ET

from .base_collector import BaseCollector
from .routing_helpers import dedupe_metrics, parse_route_category_metrics


class RoutingSummaryCollector(BaseCollector):
    """
    Collector for routing summary metrics from PAN-OS.
    Parses <show><routing><summary></summary></routing></show> XML.
    """

    def __init__(self):
        super().__init__(
            name="routing_summary_collector",
            api_command="<show><routing><summary></summary></routing></show>",
            help_text="Routing summary metrics from PAN-OS",
        )

    def parse(self, xml_data, device_config):
        metrics = []
        try:
            root = ET.fromstring(xml_data)
            device = device_config["host"]
            for entry in root.findall(".//result/entry"):
                vr_name = entry.get("name")
                if vr_name is None:
                    metrics.extend(
                        parse_route_category_metrics(
                            entry,
                            "panos_routing_summary",
                            device,
                            self.prometheus_metric,
                        )
                    )
                    continue
                bgp = entry.find("bgp")
                if bgp is None:
                    continue
                labels = {"virtual_router": vr_name}
                for elem in bgp:
                    tag = elem.tag.replace("-", "_")
                    value = (elem.text or "").strip()
                    if not value:
                        continue
                    if value in ("yes", "no"):
                        metrics.append(
                            self.prometheus_metric(
                                metric=f"panos_routing_summary_bgp_{tag}",
                                value=1 if value == "yes" else 0,
                                device=device,
                                help_text=f"BGP {tag} for virtual router {vr_name}",
                                labels=labels,
                            )
                        )
                        continue
                    try:
                        num_value = int(value)
                        metrics.append(
                            self.prometheus_metric(
                                metric=f"panos_routing_summary_bgp_{tag}",
                                value=num_value,
                                device=device,
                                help_text=f"BGP {tag} for virtual router {vr_name}",
                                labels=labels,
                            )
                        )
                    except ValueError:
                        pass
        except Exception as e:
            return self.prometheus_error_metric(
                device_config["host"], f"routing_summary_parse: {e}"
            )
        return "".join(dedupe_metrics(metrics))
