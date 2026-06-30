import os
import json
import yaml

class ConfigLoader:
    @staticmethod
    def find_config_file(start_path=None):
        if start_path is None:
            start_path = os.getcwd()
        
        for root, _, files in os.walk(start_path):
            if 'config.yaml' in files:
                return os.path.join(root, 'config.yaml')
        
        return None

    @staticmethod
    def load_config(config=None):
        """
        Load configuration and set environment variables.

        Args:
            config: One of:
                - None: auto-discovers config.yaml in the current directory tree
                - str: path to a config file (JSON or YAML)
                - dict: configuration key-value pairs to set directly

        Returns:
            dict: The loaded configuration.
        """
        # If a dict is passed, use it directly
        if isinstance(config, dict):
            for key, value in config.items():
                os.environ[key] = str(value)
            return config

        # Otherwise treat as a file path (existing behavior)
        config_path = config
        if config_path is None:
            config_path = ConfigLoader.find_config_file()

        if config_path is None or not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")

        _, ext = os.path.splitext(config_path)
        if ext.lower() == '.json':
            with open(config_path, 'r') as f:
                loaded = json.load(f)
        elif ext.lower() in ('.yaml', '.yml'):
            with open(config_path, 'r') as f:
                loaded = yaml.safe_load(f)
        else:
            raise ValueError(f"Unsupported config file format: {ext}")

        # Set environment variables
        for key, value in loaded.items():
            os.environ[key] = str(value)

        return loaded

    @staticmethod
    def get_config(key, default=None):
        return os.getenv(key, default)