import unittest
from unittest.mock import patch, MagicMock
from awschain.handlers.readers.aws_secrets_manager_secret_reader import AWSSecretsManagerSecretReader

class TestAWSSecretsManagerSecretReader(unittest.TestCase):
    def setUp(self):
        self.handler = AWSSecretsManagerSecretReader()

    @patch('awschain.handlers.readers.aws_secrets_manager_secret_reader.AWSSecretsManagerSecretReader.get_secret')
    def test_handle(self, mock_get_secret):
        mock_get_secret.return_value = {"secret_key": "secret_value"}
        request = {"aws_secret_name": "test-secret"}
        result = self.handler.handle(request)
        self.assertEqual(result["secret_key"], "secret_value")
        mock_get_secret.assert_called_once_with("test-secret")

if __name__ == '__main__':
    unittest.main()