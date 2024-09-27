import unittest
from unittest.mock import patch, MagicMock
from awschain.handlers.readers.amazon_s3_reader_handler import AmazonS3ReaderHandler

class TestAmazonS3ReaderHandler(unittest.TestCase):
    def setUp(self):
        self.handler = AmazonS3ReaderHandler()

    @patch('awschain.handlers.readers.amazon_s3_reader_handler.AmazonS3ReaderHandler.read_file_content_from_s3')
    def test_handle(self, mock_read_file):
        mock_read_file.return_value = "mocked content"
        request = {"path": "s3://test-bucket/test-object"}
        result = self.handler.handle(request)
        self.assertEqual(result["text"], "mocked content")
        mock_read_file.assert_called_once_with("test-object", "test-bucket")

if __name__ == '__main__':
    unittest.main()