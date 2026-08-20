import xml.etree.ElementTree as ET

from .base_collector import BaseCollector
from .routing_helpers import dedupe_metrics

_BGP = "<show><routing><protocol><bgp>"
_BGP_END = "</bgp></protocol></routing></show>"

BGP_COMMANDS = {
    "summary": f"{_BGP}<summary></summary>{_BGP_END}",
    "peer": f"{_BGP}<peer></peer>{_BGP_END}",
    "peer_group": f"{_BGP}<peer-group></peer-group>{_BGP_END}",
    "loc_rib_detail": f"{_BGP}<loc-rib-detail></loc-rib-detail>{_BGP_END}",
    "rib_out_detail": f"{_BGP}<rib-out-detail></rib-out-detail>{_BGP_END}",
}

PEER_NUMERIC_FIELDS = [
    "remote-as",
    "status-duration",
    "multi-hop-ttl",
    "connect-retry-interval",
    "open-delay",
    "idle-hold",
    "prefix-limit",
    "holdtime",
    "holdtime-config",
    "keepalive",
    "keepalive-config",
    "msg-update-in",
    "msg-update-out",
    "msg-total-in",
    "msg-total-out",
    "last-update-age",
    "status-flap-counts",
    "established-counts",
    "ORF-entry-received",
]

PEER_YES_NO_FIELDS = [
    "password-set",
    "passive",
    "same-confederation",
    "aggregate-confed-as",
    "nexthop-self",
    "nexthop-thirdparty",
    "nexthop-peer",
]

BGP_SUMMARY_YES_NO = [
    "reject-default-route",
    "install-route",
    "always-compare-med",
    "aggregate-regardless-med",
    "deterministic-med-processing",
    "mp-bgp-enable",
    "afi-safi-ipv4-unicast",
]

BGP_SUMMARY_NUMERIC = [
    "as-size",
    "local-as",
    "local-member-as",
    "default-local-preference",
    "rib-out-entry-current",
    "rib-out-entry-peak",
]

BGP_SUMMARY_INFO = [
    "router-id",
    "redist-default-route",
    "graceful-restart",
    "cluster-id",
]


class RoutingBgpCollector(BaseCollector):
    """
    Collector for BGP metrics from PAN-OS.
    Fetches summary, peer, peer-group, loc-rib-detail, and rib-out-detail.
    """

    def __init__(self):
        super().__init__(
            name="routing_bgp_collector",
            api_command=BGP_COMMANDS["summary"],
            help_text="BGP routing metrics from PAN-OS",
        )

    def _fetch_op(self, device_config, cmd):
        url = f"https://{device_config['host']}/api/"
        params = {
            "type": "op",
            "cmd": cmd,
            "key": device_config.get("api_key"),
        }
        response = self.session.get(
            url,
            params=params,
            verify=False,
            timeout=5,
            auth=(device_config["username"], device_config["password"]),
        )
        response.raise_for_status()
        return response.text

    def collect(self, device_config):
        metrics = []
        errors = []
        parsers = {
            "summary": self._parse_summary,
            "peer": self._parse_peer,
            "peer_group": self._parse_peer_group,
            "loc_rib_detail": self._parse_loc_rib_detail,
            "rib_out_detail": self._parse_rib_out_detail,
        }
        for subname, cmd in BGP_COMMANDS.items():
            try:
                xml_data = self._fetch_op(device_config, cmd)
                metrics.append(parsers[subname](xml_data, device_config))
            except Exception as e:
                self.logger.error(f"BGP {subname} error for device={device_config['host']}: {e}")
                errors.append(
                    self.prometheus_error_metric(
                        device_config["host"],
                        f"routing_bgp_{subname}: {e}",
                    )
                )
        if errors and not metrics:
            return errors[0]
        return "".join(errors + metrics)

    def parse(self, xml_data, device_config):
        return self._parse_summary(xml_data, device_config)

    def _parse_summary(self, xml_data, device_config):
        metrics = []
        root = ET.fromstring(xml_data)
        device = device_config["host"]
        for entry in root.findall(".//result/entry"):
            vr = entry.get("virtual-router", "unknown")
            labels = {"virtual_router": vr}
            for field in BGP_SUMMARY_NUMERIC:
                text = (entry.findtext(field) or "").strip()
                if not text:
                    continue
                tag = field.replace("-", "_")
                try:
                    metrics.append(
                        self.prometheus_metric(
                            metric=f"panos_bgp_{tag}",
                            value=int(text),
                            device=device,
                            help_text=f"BGP {tag}",
                            labels=labels,
                        )
                    )
                except ValueError:
                    pass
            for field in BGP_SUMMARY_YES_NO:
                text = (entry.findtext(field) or "").strip()
                if text not in ("yes", "no"):
                    continue
                tag = field.replace("-", "_")
                metrics.append(
                    self.prometheus_metric(
                        metric=f"panos_bgp_{tag}",
                        value=1 if text == "yes" else 0,
                        device=device,
                        help_text=f"BGP {tag} (1=yes, 0=no)",
                        labels=labels,
                    )
                )
            for field in BGP_SUMMARY_INFO:
                text = (entry.findtext(field) or "").strip()
                if not text:
                    continue
                tag = field.replace("-", "_")
                info_labels = {**labels, "value": text}
                metrics.append(
                    self.prometheus_metric(
                        metric=f"panos_bgp_{tag}_info",
                        value=1,
                        device=device,
                        help_text=f"BGP {tag}",
                        labels=info_labels,
                    )
                )
        return "".join(dedupe_metrics(metrics))

    def _parse_peer(self, xml_data, device_config):
        metrics = []
        root = ET.fromstring(xml_data)
        device = device_config["host"]
        for entry in root.findall(".//result/entry"):
            peer = entry.get("peer", "unknown")
            vr = entry.get("vr", "unknown")
            peer_group = entry.findtext("peer-group", default="unknown")
            status = entry.findtext("status", default="unknown")
            base_labels = {
                "peer": peer,
                "virtual_router": vr,
                "peer_group": peer_group,
            }
            metrics.append(
                self.prometheus_metric(
                    metric="panos_bgp_peer_up",
                    value=1 if status == "Established" else 0,
                    device=device,
                    help_text="BGP peer session up (1=Established, 0=other)",
                    labels=base_labels,
                )
            )
            metrics.append(
                self.prometheus_metric(
                    metric="panos_bgp_peer_status_info",
                    value=1,
                    device=device,
                    help_text="BGP peer status",
                    labels={**base_labels, "status": status},
                )
            )
            for field in PEER_NUMERIC_FIELDS:
                text = (entry.findtext(field) or "").strip()
                if not text:
                    continue
                tag = field.replace("-", "_").lower()
                try:
                    metrics.append(
                        self.prometheus_metric(
                            metric=f"panos_bgp_peer_{tag}",
                            value=int(text),
                            device=device,
                            help_text=f"BGP peer {tag}",
                            labels=base_labels,
                        )
                    )
                except ValueError:
                    pass
            for field in PEER_YES_NO_FIELDS:
                text = (entry.findtext(field) or "").strip()
                if text not in ("yes", "no"):
                    continue
                tag = field.replace("-", "_")
                metrics.append(
                    self.prometheus_metric(
                        metric=f"panos_bgp_peer_{tag}",
                        value=1 if text == "yes" else 0,
                        device=device,
                        help_text=f"BGP peer {tag} (1=yes, 0=no)",
                        labels=base_labels,
                    )
                )
            for info_field in ("peer-router-id", "peer-address", "local-address", "peering-type"):
                text = (entry.findtext(info_field) or "").strip()
                if not text:
                    continue
                tag = info_field.replace("-", "_")
                metrics.append(
                    self.prometheus_metric(
                        metric=f"panos_bgp_peer_{tag}_info",
                        value=1,
                        device=device,
                        help_text=f"BGP peer {tag}",
                        labels={**base_labels, "value": text},
                    )
                )
            for counter in entry.findall(".//prefix-counter/entry"):
                afi_safi = counter.get("afi-safi", "unknown")
                counter_labels = {**base_labels, "afi_safi": afi_safi}
                for field in counter:
                    text = (field.text or "").strip()
                    if not text:
                        continue
                    tag = field.tag.replace("-", "_")
                    try:
                        metrics.append(
                            self.prometheus_metric(
                                metric=f"panos_bgp_peer_prefix_{tag}",
                                value=int(text),
                                device=device,
                                help_text=f"BGP peer prefix counter {tag}",
                                labels=counter_labels,
                            )
                        )
                    except ValueError:
                        pass
        return "".join(dedupe_metrics(metrics))

    def _parse_peer_group(self, xml_data, device_config):
        metrics = []
        root = ET.fromstring(xml_data)
        device = device_config["host"]
        for entry in root.findall(".//result/entry"):
            peer_group = entry.get("peer-group", "unknown")
            vr = entry.get("vr", "unknown")
            labels = {"peer_group": peer_group, "virtual_router": vr}
            pg_type = entry.findtext("type", default="unknown")
            metrics.append(
                self.prometheus_metric(
                    metric="panos_bgp_peer_group_info",
                    value=1,
                    device=device,
                    help_text="BGP peer group",
                    labels={**labels, "type": pg_type},
                )
            )
            for field in (
                "aggregate-confed-as",
                "soft-reset-support",
                "nexthop-self",
                "nexthop-thirdparty",
                "nexthop-peer",
            ):
                text = (entry.findtext(field) or "").strip()
                if text not in ("yes", "no"):
                    continue
                tag = field.replace("-", "_")
                metrics.append(
                    self.prometheus_metric(
                        metric=f"panos_bgp_peer_group_{tag}",
                        value=1 if text == "yes" else 0,
                        device=device,
                        help_text=f"BGP peer group {tag} (1=yes, 0=no)",
                        labels=labels,
                    )
                )
        return "".join(dedupe_metrics(metrics))

    def _parse_loc_rib_detail(self, xml_data, device_config):
        metrics = []
        root = ET.fromstring(xml_data)
        device = device_config["host"]
        for entry in root.findall(".//result/entry"):
            vr = entry.get("vr", "unknown")
            for member in entry.findall(".//loc-rib/member"):
                prefix = member.findtext("prefix", default="unknown")
                flag = (member.findtext("flag") or "").strip()
                labels = {
                    "virtual_router": vr,
                    "prefix": prefix,
                    "nexthop": (member.findtext("nexthop") or "").strip(),
                    "received_from": member.findtext("received-from", default="unknown"),
                    "as_path": member.findtext("as-path", default=""),
                    "best": "yes" if "*" in flag else "no",
                }
                metrics.append(
                    self.prometheus_metric(
                        metric="panos_bgp_loc_rib_route_info",
                        value=1,
                        device=device,
                        help_text="BGP local RIB route entry",
                        labels=labels,
                    )
                )
                attr = member.find("attr")
                if attr is not None:
                    for field in ("weight", "med", "local-preference"):
                        text = (attr.findtext(field) or "").strip()
                        if not text:
                            continue
                        tag = field.replace("-", "_")
                        try:
                            metrics.append(
                                self.prometheus_metric(
                                    metric=f"panos_bgp_loc_rib_{tag}",
                                    value=int(text),
                                    device=device,
                                    help_text=f"BGP local RIB {tag}",
                                    labels=labels,
                                )
                            )
                        except ValueError:
                            pass
                flap = member.find("flap-stat")
                if flap is not None:
                    for field in ("flap-value", "flap-count"):
                        text = (flap.findtext(field) or "").strip()
                        if not text:
                            continue
                        tag = field.replace("-", "_")
                        try:
                            value = float(text) if field == "flap-value" else int(text)
                            metrics.append(
                                self.prometheus_metric(
                                    metric=f"panos_bgp_loc_rib_{tag}",
                                    value=value,
                                    device=device,
                                    help_text=f"BGP local RIB {tag}",
                                    labels=labels,
                                )
                            )
                        except ValueError:
                            pass
        return "".join(dedupe_metrics(metrics))

    def _parse_rib_out_detail(self, xml_data, device_config):
        metrics = []
        root = ET.fromstring(xml_data)
        device = device_config["host"]
        for entry in root.findall(".//result/entry"):
            vr = entry.get("vr", "unknown")
            for member in entry.findall(".//rib-out/member"):
                labels = {
                    "virtual_router": vr,
                    "prefix": member.findtext("prefix", default="unknown"),
                    "peer": member.findtext("peer", default="unknown"),
                    "nexthop": (member.findtext("nexthop") or "").strip(),
                    "advertise_status": member.findtext("advertise-status", default="unknown"),
                    "as_path": member.findtext("as-path", default=""),
                }
                metrics.append(
                    self.prometheus_metric(
                        metric="panos_bgp_rib_out_route_info",
                        value=1,
                        device=device,
                        help_text="BGP RIB-out route entry",
                        labels=labels,
                    )
                )
                attr = member.find("attr")
                if attr is not None:
                    for field in ("med", "local-preference"):
                        text = (attr.findtext(field) or "").strip()
                        if not text:
                            continue
                        tag = field.replace("-", "_")
                        try:
                            metrics.append(
                                self.prometheus_metric(
                                    metric=f"panos_bgp_rib_out_{tag}",
                                    value=int(text),
                                    device=device,
                                    help_text=f"BGP RIB-out {tag}",
                                    labels=labels,
                                )
                            )
                        except ValueError:
                            pass
        return "".join(dedupe_metrics(metrics))
