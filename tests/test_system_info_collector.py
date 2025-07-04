import pytest
from app.collectors.system_info_collector import SystemInfoCollector

SAMPLE_XML = '''
<response status="success">
  <result>
    <system>
      <uptime>0 days, 20:32:51</uptime>
      <sw-version>10.1.0</sw-version>
      <model>PA-220</model>
      <serial>1234567890</serial>
      <multi-vsys>off</multi-vsys>
      <operational-mode>normal</operational-mode>
      <device-certificate-status>valid</device-certificate-status>
      <mac_count>5</mac_count>
    </system>
  </result>
</response>
'''

def test_parse_system_info():
    collector = SystemInfoCollector()
    device_config = {'host': '192.168.1.1'}
    metrics = collector.parse(SAMPLE_XML, device_config)
    assert 'panos_system_uptime_seconds' in metrics
    assert 'panos_system_software_version_info' in metrics
    assert 'panos_system_model_info' in metrics
    assert 'panos_system_serial_info' in metrics
    assert 'panos_system_multi_vsys_enabled' in metrics
    assert 'panos_system_operational_mode_info' in metrics
    assert 'panos_system_device_certificate_status_info' in metrics
    assert 'panos_system_mac_count' in metrics 