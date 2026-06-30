import os
import tempfile
import unittest
from unittest.mock import patch

from awschain.handlers.processors.prompt_handler import PromptHandler


class TestPromptHandlerInlineTemplate(unittest.TestCase):
    """Tests for PromptHandler with inline prompt_template."""

    def setUp(self):
        self.handler = PromptHandler()

    def test_inline_template_formats_input_text(self):
        request = {
            "text": "Hello world",
            "prompt_template": "Summarize: {input_text}",
        }
        self.handler.handle(request)

        self.assertEqual(request["text"], "Summarize: Hello world")

    def test_inline_template_with_empty_text(self):
        request = {
            "text": "",
            "prompt_template": "Process this: {input_text}",
        }
        self.handler.handle(request)

        self.assertEqual(request["text"], "Process this: ")

    def test_inline_template_with_no_text_key(self):
        request = {
            "prompt_template": "No input provided: {input_text}",
        }
        self.handler.handle(request)

        self.assertEqual(request["text"], "No input provided: ")

    def test_inline_template_with_complex_text(self):
        long_text = "Line 1\nLine 2\nLine 3 with special chars: <>&\""
        request = {
            "text": long_text,
            "prompt_template": "Analyze the following:\n{input_text}\n\nProvide insights.",
        }
        self.handler.handle(request)

        expected = f"Analyze the following:\n{long_text}\n\nProvide insights."
        self.assertEqual(request["text"], expected)

    def test_inline_template_takes_priority_over_prompt_file_name(self):
        """If both prompt_template and prompt_file_name are set, inline wins."""
        request = {
            "text": "test",
            "prompt_template": "Inline: {input_text}",
            "prompt_file_name": "nonexistent_file",
        }
        # Should NOT raise FileNotFoundError because inline takes priority
        self.handler.handle(request)

        self.assertEqual(request["text"], "Inline: test")


class TestPromptHandlerFileBased(unittest.TestCase):
    """Tests for backward-compatible file-based prompt loading."""

    def setUp(self):
        self.handler = PromptHandler()

    def test_falls_back_to_file_when_no_inline_template(self):
        """Without prompt_template, should try to load from file."""
        request = {
            "text": "some content",
            "prompt_file_name": "nonexistent_prompt_file_xyz",
        }
        # The handler catches FileNotFoundError and uses a default prompt
        self.handler.handle(request)

        # Should contain the text, formatted with the fallback default prompt
        self.assertIn("some content", request["text"])

    def test_uses_default_prompt_file_when_no_keys_set(self):
        """With no prompt_template and no prompt_file_name, uses default_prompt."""
        request = {"text": "my input"}

        # Will try to load ./prompts/default_prompt.txt
        # If it doesn't exist, falls back to a hardcoded default
        self.handler.handle(request)

        self.assertIn("my input", request["text"])

    def test_loads_prompt_from_actual_file(self):
        """Test loading from an actual prompt file on disk."""
        # Create a temporary prompts directory and file
        original_dir = os.getcwd()
        tmpdir = tempfile.mkdtemp()
        prompts_dir = os.path.join(tmpdir, "prompts")
        os.makedirs(prompts_dir)

        prompt_content = "Custom file prompt: {input_text}"
        with open(os.path.join(prompts_dir, "test_prompt.txt"), "w") as f:
            f.write(prompt_content)

        os.chdir(tmpdir)
        try:
            request = {
                "text": "file-based input",
                "prompt_file_name": "test_prompt",
            }
            self.handler.handle(request)

            self.assertEqual(request["text"], "Custom file prompt: file-based input")
        finally:
            os.chdir(original_dir)


if __name__ == "__main__":
    unittest.main()
