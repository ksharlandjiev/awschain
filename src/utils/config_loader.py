import os
import json
import yaml

class ConfigLoader:
    @staticmethod
    def load_config(config_path):
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")

        _, ext = os.path.splitext(config_path)
        if ext.lower() == '.json':
            with open(config_path, 'r') as f:
                config = json.load(f)
        elif ext.lower() in ('.yaml', '.yml'):
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
        else:
            raise ValueError(f"Unsupported config file format: {ext}")

        # Set environment variables
        for key, value in config.items():
            os.environ[key] = str(value)

        return config

    @staticmethod
    def get_config(key, default=None):
        return os.getenv(key, default)