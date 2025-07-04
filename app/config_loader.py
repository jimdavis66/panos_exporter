import yaml
import logging

class ConfigLoader:
    """
    Loads and validates YAML config for panos_exporter.
    Ensures required fields and valid collector names.
    """
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = None
        self.logger = logging.getLogger("panos_exporter.config_loader")

    def load(self):
        """
        Load and validate YAML config from file.
        Raises ValueError on schema errors.
        """
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.validate()
        return self.config

    def validate(self):
        """
        Validate config schema: devices must have username/password, collectors must be known.
        Logs and raises errors on invalid config.
        """
        if 'devices' not in self.config or not isinstance(self.config['devices'], dict):
            self.logger.error("Config missing 'devices' dict")
            raise ValueError("Config missing 'devices' dict")
        for dev, info in self.config['devices'].items():
            if not isinstance(info, dict):
                self.logger.error(f"Device {dev} config is not a dict")
                raise ValueError(f"Device {dev} config is not a dict")
            if 'username' not in info or 'password' not in info:
                self.logger.error(f"Device {dev} missing username or password")
                raise ValueError(f"Device {dev} missing username or password")
        if 'collectors' in self.config:
            known = set([
                'system_info_collector',
                'system_environmentals_collector',
                'global_counter_collector',
                'session_collector',
                'interface_collector',
                'interface_counter_collector',
                'data_processor_resource_utilization_collector',
            ])
            if not isinstance(self.config['collectors'], list):
                self.logger.error("'collectors' must be a list")
                raise ValueError("'collectors' must be a list")
            for c in self.config['collectors']:
                if c not in known:
                    self.logger.error(f"Unknown collector: {c}")
                    raise ValueError(f"Unknown collector: {c}")

    def get_device(self, target):
        """
        Return device config for the given target.
        Raises ValueError if not found.
        """
        if self.config is None:
            self.load()
        devices = self.config.get('devices', {})
        if target not in devices:
            raise ValueError(f"Target {target} not found in config")
        return devices[target]
