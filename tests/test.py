from awschain import HandlerFactory, ConfigLoader

# Your test logic follows...
reader = HandlerFactory.get_handler("LocalFileReaderHandler")
prompt_handler = HandlerFactory.get_handler("PromptHandler")
transformer = HandlerFactory.get_handler("AmazonBedrockHandler")
writer = HandlerFactory.get_handler("LocalFileWriterHandler")

# Set up the chain
# reader.set_next(prompt_handler)
# .set_next(transformer).set_next(writer)

ConfigLoader.load_config()

# Define the request
request = {"path": "/Users/awskamen/Downloads/example.txt", "write_file_path": "/Users/awskamen/Downloads/output.txt", "prompt": "default_prompt"}

# Execute the chain
reader.set_next(prompt_handler).set_next(transformer)


response = reader.handle(request)

print(response)