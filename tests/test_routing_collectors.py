from app.collectors.routing_bgp_collector import RoutingBgpCollector
from app.collectors.routing_resource_collector import RoutingResourceCollector
from app.collectors.routing_route_collector import RoutingRouteCollector
from app.collectors.routing_summary_collector import RoutingSummaryCollector

DEVICE = {"host": "192.168.1.25"}

RESOURCE_XML = """
<response status="success">
<result>
<entry>
<All-Routes><total>51</total><limit>20000</limit><active>49</active></All-Routes>
<Static-Routes><total>14</total></Static-Routes>
<BGP-Routes><total>1</total></BGP-Routes>
</entry>
</result>
</response>
"""

SUMMARY_XML = """
<response status="success">
<result>
<entry>
<All-Routes><total>51</total><limit>20000</limit><active>49</active></All-Routes>
<BGP-Routes><total>1</total></BGP-Routes>
</entry>
<entry name="default">
<bgp>
<peer-group-count>2</peer-group-count>
<peer-count>2</peer-count>
<local-rib-prefix-count>3</local-rib-prefix-count>
<mp-bgp-enable>yes</mp-bgp-enable>
</bgp>
</entry>
</result>
</response>
"""

ROUTE_XML = """
<response status="success">
<result>
<entry>
<virtual-router>default</virtual-router>
<destination>0.0.0.0/0</destination>
<nexthop>14.203.227.233</nexthop>
<metric/>
<flags>A?B </flags>
<age>101265</age>
<interface/>
<route-table>unicast</route-table>
</entry>
<entry>
<virtual-router>default</virtual-router>
<destination>10.0.32.0/28</destination>
<nexthop>192.168.201.5</nexthop>
<metric>10</metric>
<flags>A S </flags>
<age/>
<interface>ethernet1/15</interface>
<route-table>unicast</route-table>
</entry>
</result>
</response>
"""

BGP_SUMMARY_XML = """
<response status="success">
<result>
<entry virtual-router="default">
<router-id>14.203.227.218</router-id>
<local-as>4294900943</local-as>
<mp-bgp-enable>yes</mp-bgp-enable>
<rib-out-entry-current>2</rib-out-entry-current>
</entry>
</result>
</response>
"""

BGP_PEER_XML = """
<response status="success">
<result>
<entry peer="PE1" vr="default">
<peer-group>TPG-PE1</peer-group>
<remote-as>2764</remote-as>
<status>Established</status>
<status-duration>101358</status-duration>
<prefix-counter>
<entry afi-safi="bgpAfiIpv4-unicast">
<incoming-total>1</incoming-total>
<incoming-accepted>1</incoming-accepted>
</entry>
</prefix-counter>
</entry>
</result>
</response>
"""

BGP_PEER_GROUP_XML = """
<response status="success">
<result>
<entry peer-group="TPG-PE1" vr="default">
<type>eBGP</type>
<nexthop-thirdparty>yes</nexthop-thirdparty>
</entry>
</result>
</response>
"""

BGP_LOC_RIB_XML = """
<response status="success">
<result>
<entry vr="default">
<loc-rib>
<member>
<prefix>0.0.0.0/0</prefix>
<flag>*</flag>
<nexthop>14.203.227.233</nexthop>
<received-from>PE1</received-from>
<as-path>2764</as-path>
<attr><med>0</med><local-preference>200</local-preference></attr>
<flap-stat><flap-count>0</flap-count></flap-stat>
</member>
</loc-rib>
</entry>
</result>
</response>
"""

BGP_RIB_OUT_XML = """
<response status="success">
<result>
<entry vr="default">
<rib-out>
<member>
<prefix>203.25.195.0/24</prefix>
<nexthop>14.203.227.234</nexthop>
<peer>PE1</peer>
<advertise-status>advertised</advertise-status>
<as-path>4294900943</as-path>
<attr><med>0</med><local-preference>0</local-preference></attr>
</member>
</rib-out>
</entry>
</result>
</response>
"""


def test_parse_routing_resource():
    metrics = RoutingResourceCollector().parse(RESOURCE_XML, DEVICE)
    assert "panos_routing_resource_total" in metrics
    assert 'category="all_routes"' in metrics
    assert "panos_routing_resource_active" in metrics


def test_parse_routing_summary():
    metrics = RoutingSummaryCollector().parse(SUMMARY_XML, DEVICE)
    assert "panos_routing_summary_total" in metrics
    assert "panos_routing_summary_bgp_peer_count" in metrics
    assert 'virtual_router="default"' in metrics


def test_parse_routing_route():
    metrics = RoutingRouteCollector().parse(ROUTE_XML, DEVICE)
    assert "panos_routing_route_info" in metrics
    assert 'destination="0.0.0.0/0"' in metrics
    assert "panos_routing_route_age_seconds" in metrics
    assert "panos_routing_route_metric" in metrics


def test_parse_bgp_summary():
    metrics = RoutingBgpCollector()._parse_summary(BGP_SUMMARY_XML, DEVICE)
    assert "panos_bgp_local_as" in metrics
    assert "panos_bgp_router_id_info" in metrics
    assert "panos_bgp_rib_out_entry_current" in metrics


def test_parse_bgp_peer():
    metrics = RoutingBgpCollector()._parse_peer(BGP_PEER_XML, DEVICE)
    assert "panos_bgp_peer_up" in metrics
    assert "panos_bgp_peer_remote_as" in metrics
    assert "panos_bgp_peer_prefix_incoming_total" in metrics


def test_parse_bgp_peer_group():
    metrics = RoutingBgpCollector()._parse_peer_group(BGP_PEER_GROUP_XML, DEVICE)
    assert "panos_bgp_peer_group_info" in metrics
    assert "panos_bgp_peer_group_nexthop_thirdparty" in metrics


def test_parse_bgp_loc_rib_detail():
    metrics = RoutingBgpCollector()._parse_loc_rib_detail(BGP_LOC_RIB_XML, DEVICE)
    assert "panos_bgp_loc_rib_route_info" in metrics
    assert 'best="yes"' in metrics
    assert "panos_bgp_loc_rib_local_preference" in metrics


def test_parse_bgp_rib_out_detail():
    metrics = RoutingBgpCollector()._parse_rib_out_detail(BGP_RIB_OUT_XML, DEVICE)
    assert "panos_bgp_rib_out_route_info" in metrics
    assert 'peer="PE1"' in metrics
