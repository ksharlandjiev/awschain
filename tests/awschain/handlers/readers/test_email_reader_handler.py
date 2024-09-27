import unittest
from unittest.mock import patch, MagicMock
from awschain.handlers.readers.email_reader_handler import EmailReaderHandler

class TestEmailReaderHandler(unittest.TestCase):
    def setUp(self):
        self.handler = EmailReaderHandler()

    @patch('awschain.handlers.readers.email_reader_handler.EmailReaderHandler.read_one_unread_email')
    def test_handle(self, mock_read_email):
        mock_read_email.return_value = {"subject": "Test Subject", "body": "Test Body"}
        request = {
            "imap_server": "test.server.com",
            "email_username": "test@example.com",
            "email_password": "password123"
        }
        result = self.handler.handle(request)
        self.assertEqual(result["subject"], "Test Subject")
        self.assertEqual(result["body"], "Test Body")
        mock_read_email.assert_called_once()

if __name__ == '__main__':
    unittest.main()