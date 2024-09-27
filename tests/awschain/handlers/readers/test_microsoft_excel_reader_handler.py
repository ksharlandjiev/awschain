import unittest
from unittest.mock import patch, MagicMock
from awschain.handlers.readers.microsoft_excel_reader_handler import MicrosoftExcelReaderHandler

class TestMicrosoftExcelReaderHandler(unittest.TestCase):
    def setUp(self):
        self.handler = MicrosoftExcelReaderHandler()

    @patch('awschain.handlers.readers.microsoft_excel_reader_handler.load_workbook')
    def test_handle(self, mock_load_workbook):
        mock_workbook = MagicMock()
        mock_sheet = MagicMock()
        mock_sheet.title = "Sheet1"
        mock_sheet.iter_rows.return_value = [("Cell1", "Cell2"), ("Cell3", "Cell4")]
        mock_workbook.__iter__.return_value = [mock_sheet]
        mock_load_workbook.return_value = mock_workbook

        request = {"path": "/path/to/test.xlsx"}
        result = self.handler.handle(request)

        expected_text = "Sheet: Sheet1\nCell1\tCell2\t\nCell3\tCell4\t\n"
        self.assertEqual(result["text"], expected_text)
        mock_load_workbook.assert_called_once_with("/path/to/test.xlsx", data_only=True)

if __name__ == '__main__':
    unittest.main()