import unittest
from unittest.mock import patch, mock_open
from awschain.handlers.readers.local_file_reader_handler import LocalFileReaderHandler

class TestLocalFileReaderHandler(unittest.TestCase):
    def setUp(self):
        self.handler = LocalFileReaderHandler()

    @patch("builtins.open", new_callable=mock_open, read_data="test file content")
    def test_handle(self, mock_file):
        request = {"path": "/path/to/test/file.txt"}
        result = self.handler.handle(request)

        self.assertEqual(result["text"], "test file content")
        mock_file.assert_called_once_with("/path/to/test/file.txt", 'r', encoding='utf-8')

if __name__ == '__main__':
    unittest.main()