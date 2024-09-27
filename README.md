
# awschain

`awschain` is a Python package that provides a flexible and extensible implementation of the **Chain of Responsibility** design pattern. It allows users to chain together multiple processing steps in a sequence of handlers, making it easier to create dynamic and modular processing pipelines. This package is ideal for scenarios where various operations need to be applied in sequence, such as file processing, API interactions, and data transformations.

## Features

- **Chain of Responsibility Pattern**: Easily define processing chains with different handlers performing specialized tasks.
- **Modular and Extensible**: Customize the chain by adding or removing handlers as needed.
- **Predefined Handlers**: A set of built-in handlers is provided for common tasks.
- **Dynamic Handler Discovery**: Automatically identify and instantiate handlers using the Factory pattern.
- **Seamless Integration**: Designed to integrate with larger applications, particularly when task delegation and flexible processing pipelines are required.

## Installation

You can install `awschain` directly from PyPI:

```bash
pip install awschain
```

## Usage

## Example Use Case

Let’s say you want to process files by first reading their content, performing a summarization using Generative AI, and then writing the results to another location. You can achieve this by defining a chain with three handlers: `LocalFileReaderHandler`, `PromptHandler`, `AmazonBedrockHandler`, and `LocalFileWriterHandler`.

```python
from awschain import HandlerFactory, ConfigLoader

# Load config
ConfigLoader.load_config("/path/to/config.yaml")

# Create the handlers
reader = HandlerFactory.get_handler("LocalFileReaderHandler")
prompt_handler = HandlerFactory.get_handler("PromptHandler")
transformer = HandlerFactory.get_handler("AmazonBedrockHandler")
writer = HandlerFactory.get_handler("LocalFileWriterHandler")

# Set up the chain
reader.set_next(prompt_handler).set_next(transformer).set_next(writer)

# Please store your prompt in your root of your project in prompts folder. Example: prompts/default_prompt.txt

# Define the request
request = {"file_path": "example.txt", "write_file_path": "output.txt", "prompt": "default_prompt"}

# Execute the chain
reader.handle(request)
```

### Built-in Handlers

`awschain` comes with several predefined handlers that can be used right out of the box. Examples include:

Readers:
- **LocalFileReaderHandler**: Handles local audio, video, and text files for processing.
- **S3ReaderHandler**: Manages the reading and downloading of S3 objects (files) from Amazon S3.
= **HTTPHandler**: Generic HTTP handler that allows you to fetch HTML data from http(s) endpoints. It uses BeautifulSoup to clean HTML tags.

- **PDFReaderHandler**: Extracts text from PDF documents for summarization.
- **MicrosoftExcelReaderHandler**: Extract text from Microsoft Excel documents.
- **MicrosoftWordReaderHandler**: Extract text from Microsoft Word documents.
- **QuipReaderHandler**: Extract text from Quip document.
- **YouTubeReaderHandler**: Downloads videos from YouTube URLs and extracts audio.

Processors:
- **AmazonBedrockHandler**: Summarizes text content using Amazon Bedrock.
- **AmazonBedrockChatHandler**: Used to perform interactive chat with Amazon Bedrock using the messages API.
- **AmazonComprehendInsightsHandler**: Extract valuable insights from your data using Amazon Comprehend NLP capabilities.
- **AmazonComprehendPIIHandler**, **AmazonComprehendPIITokenizeHandler** and **AmazonComprehendPIIUntokenizeHandler**: Used to detect, tokenize and untokenize PII data in your text retaining the context and allowing downstream services such as Bedrock to process the data without PII.
- **AmazonTranscriptionHandler**: Transcribes audio files into text using Amazon Transcribe.
- **AmazonTextractHandler**: Extracts text from images such as .jpg, .png, .tiff
- **HTMLCleanerHandler**: Used to clean HTML tags when consuming web page / HTML documents.
- **PromptHandler**: Uses a minimalistic prompt framework - all your prompts can be stored in the prompts/ folder and you can select which prompt to use when invoking the main.py.

Writers:
- **S3WriterHandler**: Manages the uploading of of S3 objects (files) to Amazon S3.
- **LocalFileWriterHandler**: Writes output into a local file.
- **ClipboardWriterHandler**: Writes output into clipboard.

You can also create your own custom handlers by extending the base `Handler` class.

## Extending awschain

If you need to add custom functionality, you can extend the framework by writing custom handlers and integrating them into the chain.

To create a custom handler, simply subclass the `AbstractHandler` class and implement the `handle` method:

```python
from awschainhandlers.abstract_handler import AbstractHandler

class CustomHandler(AbstractHandler):
    def handle(self, request):
        # Process the request
        if request.get("custom"):
            print("Handling custom request.")
        # Pass to the next handler in the chain if applicable
        return super().handle(request)
```

## Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request if you have ideas to improve `awschain`.

## License

`awschain` is licensed under the MIT License.
