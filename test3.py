# test3.py
# Glue Interactive Sessions compatible — no local files required.
# Requires: awschain==0.1.1.3
#
# In a Glue notebook, add this magic in the first cell:
#   %additional_python_modules awschain==0.1.1.3

from awschain import HandlerFactory, ConfigLoader

# ── Config (no file needed) ────────────────────────────────────────────────
ConfigLoader.load_config({
    "AWS_DEFAULT_REGION": "us-east-1",
    "BUCKET_NAME": "515232103838-transcribe",
    "S3_FOLDER": "uploads/",
    "OUTPUT_FOLDER": "transcriptions/",
    "AMAZON_BEDROCK_MODEL_ID": "us.anthropic.claude-sonnet-4-6",
    "AMAZON_BEDROCK_MODEL_PROPS": '{"max_tokens":4096, "anthropic_version": "bedrock-2023-05-31", "messages": [{"role": "user", "content": ""}]}',
    "AMAZON_BEDROCK_PROMPT_TEMPLATE": "{prompt_text}",
    "AMAZON_BEDROCK_PROMPT_INPUT_VAR": "$.messages[0].content",
    "AMAZON_BEDROCK_OUTPUT_JSONPATH": "$.content[0].text",
    "DIR_STORAGE": "/tmp/downloads",
    "MAX_PARALLEL_PROCESSES": "30",
    "CLIPBOARD_COPY": "false",
})

# ── Handlers ───────────────────────────────────────────────────────────────
reader  = HandlerFactory.get_handler("AmazonS3ReaderHandler")
prompt  = HandlerFactory.get_handler("PromptHandler")
bedrock = HandlerFactory.get_handler("AmazonBedrockHandler")
#writer  = HandlerFactory.get_handler("AmazonS3WriterHandler")

reader.set_next(prompt).set_next(bedrock)
#.set_next(writer)

# ── Request (no local file paths) ─────────────────────────────────────────
request = {
    "path": "s3://515232103838-transcribe/uploads/example.txt",
#    "write_file_path": "s3://515232103838-transcribe/transcriptions/output.txt",
    "prompt_template": (
        "Please provide a 300 word minimum summary highlighting the most important topics "
        "from the following text: {input_text}.\n\n--\n"
        "Do not provide an entry line such as: 'Here is a summary of key points from the text:', "
        "instead just start with the summary."
    ),
}

# ── Execute ────────────────────────────────────────────────────────────────
result = reader.handle(request)
print("Done. Output text:", result.get("text"))