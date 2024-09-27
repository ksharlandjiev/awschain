import unittest
from awschain import HandlerFactory, ConfigLoader

class TestAWSChain(unittest.TestCase):
    def setUp(self):
        ConfigLoader.load_config()
        self.reader = HandlerFactory.get_handler("LocalFileReaderHandler")
        self.prompt_handler = HandlerFactory.get_handler("PromptHandler")
        self.transformer = HandlerFactory.get_handler("AmazonBedrockHandler")
        self.writer = HandlerFactory.get_handler("LocalFileWriterHandler")

    def test_chain_execution(self):
        # Set up the chain
        self.reader.set_next(self.prompt_handler).set_next(self.transformer)

        # Define the request
        request = {
            "path": "/Users/awskamen/Downloads/example.txt",
            "write_file_path": "/Users/awskamen/Downloads/output.txt",
            "prompt": "default_prompt"
        }

        # Execute the chain
        response = self.reader.handle(request)

        # Add assertions here
        self.assertIsNotNone(response)
        # Add more specific assertions based on expected behavior

if __name__ == "__main__":
    unittest.main()