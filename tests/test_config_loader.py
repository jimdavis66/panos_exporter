import pytest
from app.config_loader import ConfigLoader
import tempfile
import yaml

VALID_CONFIG = {
    'devices': {
        '192.168.1.1': {'username': 'u', 'password': 'p'}
    },
    'collectors': [
        'system_info_collector',
        'system_environmentals_collector',
    ]
}

INVALID_CONFIG_MISSING_USER = {
    'devices': {
        '192.168.1.1': {'password': 'p'}
    }
}

INVALID_CONFIG_COLLECTOR = {
    'devices': {
        '192.168.1.1': {'username': 'u', 'password': 'p'}
    },
    'collectors': ['not_a_real_collector']
}

def write_temp_yaml(data):
    f = tempfile.NamedTemporaryFile('w+', delete=False)
    yaml.dump(data, f)
    f.close()
    return f.name

def test_valid_config():
    path = write_temp_yaml(VALID_CONFIG)
    loader = ConfigLoader(path)
    config = loader.load()
    assert 'devices' in config
    assert 'collectors' in config

def test_missing_username():
    path = write_temp_yaml(INVALID_CONFIG_MISSING_USER)
    loader = ConfigLoader(path)
    with pytest.raises(ValueError):
        loader.load()

def test_invalid_collector():
    path = write_temp_yaml(INVALID_CONFIG_COLLECTOR)
    loader = ConfigLoader(path)
    with pytest.raises(ValueError):
        loader.load() 