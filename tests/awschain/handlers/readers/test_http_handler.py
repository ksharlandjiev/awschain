import unittest
from unittest.mock import patch, MagicMock
from awschain.handlers.readers.http_handler import HTTPHandler

class TestHTTPHandler(unittest.TestCase):
    def setUp(self):
        self.handler = HTTPHandler()

    @patch('awschain.handlers.readers.http_handler.fetch_webpage')
    @patch('awschain.handlers.readers.http_handler.BeautifulSoup')
    def test_handle(self, mock_bs, mock_fetch):
        mock_fetch.return_value = "HTML content"
        mock_soup = MagicMock()
        mock_soup.get_text.return_value = "Extracted text"
        mock_bs.return_value = mock_soup

        request = {"path": "http://example.com"}
        result = self.handler.handle(request)

        self.assertEqual(result["text"], "Extracted text")
        mock_fetch.assert_called_once_with("http://example.com")
        mock_bs.assert_called_once_with("HTML content", 'html.parser')

if __name__ == '__main__':
    unittest.main()