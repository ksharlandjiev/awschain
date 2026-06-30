import os
import json
import tempfile
import unittest

from awschain.utils.config_loader import ConfigLoader


class TestConfigLoaderWithDict(unittest.TestCase):
    """Tests for ConfigLoader.load_config() accepting a dict."""

    def setUp(self):
        # Clean up env vars we'll be setting
        self._keys = ["TEST_REGION", "TEST_MODEL_ID", "TEST_NUMERIC"]
        for key in self._keys:
            os.environ.pop(key, None)

    def tearDown(self):
        for key in self._keys:
            os.environ.pop(key, None)

    def test_dict_sets_env_vars(self):
        config = {
            "TEST_REGION": "us-west-2",
            "TEST_MODEL_ID": "anthropic.claude-v2",
        }
        result = ConfigLoader.load_config(config)

        self.assertEqual(result, config)
        self.assertEqual(os.environ["TEST_REGION"], "us-west-2")
        self.assertEqual(os.environ["TEST_MODEL_ID"], "anthropic.claude-v2")

    def test_dict_converts_non_string_values_to_str(self):
        config = {"TEST_NUMERIC": 4096}
        ConfigLoader.load_config(config)

        self.assertEqual(os.environ["TEST_NUMERIC"], "4096")

    def test_dict_returns_original_dict(self):
        config = {"TEST_REGION": "eu-west-1"}
        result = ConfigLoader.load_config(config)

        self.assertIs(result, config)

    def test_empty_dict_is_valid(self):
        result = ConfigLoader.load_config({})
        self.assertEqual(result, {})


class TestConfigLoaderWithFilePath(unittest.TestCase):
    """Tests for backward-compatible file-based config loading."""

    def test_loads_yaml_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("MY_TEST_KEY: my_value\n")
            f.flush()
            path = f.name

        try:
            result = ConfigLoader.load_config(path)
            self.assertEqual(result["MY_TEST_KEY"], "my_value")
            self.assertEqual(os.environ["MY_TEST_KEY"], "my_value")
        finally:
            os.unlink(path)
            os.environ.pop("MY_TEST_KEY", None)

    def test_loads_json_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"JSON_TEST_KEY": "json_value"}, f)
            f.flush()
            path = f.name

        try:
            result = ConfigLoader.load_config(path)
            self.assertEqual(result["JSON_TEST_KEY"], "json_value")
            self.assertEqual(os.environ["JSON_TEST_KEY"], "json_value")
        finally:
            os.unlink(path)
            os.environ.pop("JSON_TEST_KEY", None)

    def test_raises_on_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            ConfigLoader.load_config("/nonexistent/path/config.yaml")

    def test_raises_on_unsupported_extension(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write("key = 'value'\n")
            path = f.name

        try:
            with self.assertRaises(ValueError):
                ConfigLoader.load_config(path)
        finally:
            os.unlink(path)


class TestConfigLoaderAutoDiscover(unittest.TestCase):
    """Tests for auto-discovery (None argument)."""

    def test_none_discovers_config_yaml_in_cwd(self):
        # This test relies on config.yaml existing in the project root.
        # Run from project root for this to pass.
        original_dir = os.getcwd()
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        os.chdir(project_root)

        try:
            result = ConfigLoader.load_config(None)
            self.assertIsInstance(result, dict)
            self.assertGreater(len(result), 0)
        finally:
            os.chdir(original_dir)


if __name__ == "__main__":
    unittest.main()
