from typing import Any
from ..abstract_handler import AbstractHandler
class LocalFileReaderHandler(AbstractHandler):
            
    def handle(self, request: dict) -> dict:
        file_path = request.get("path")
        if not file_path and self.path:
            file_path = self.path

        text = self.read_text_content(file_path)
        request.update({"text": text})

        return super().handle(request)
    
    def configure(self, config):
        self.path = config.get("path")

    def read_text_content(self, file_path):
        """
        Reads and returns the content of a text or JSON file.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return ""