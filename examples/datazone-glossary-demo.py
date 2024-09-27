#!/opt/anaconda3/bin/python

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import os
import sys
from typing import Any
from dotenv import load_dotenv
from awschain import HandlerFactory, ConfigLoader
import argparse

# Load config
ConfigLoader.load_config()

def determine_input_type(file_path):
    if "youtube" in file_path or "youtu.be" in file_path:
        return "youtube_url"
    elif file_path.startswith(('http')):
        return "http"    
    elif file_path.startswith(('s3://')):
        return "s3"  
    elif file_path.startswith(('quip://')):
        return "quip"   
    elif file_path.endswith(('.mp3', '.mp4', '.m4a', '.wav', '.flac', '.mov', '.avi')):
        return "multimedia_file"
    elif file_path.endswith('.pdf'):
        return "pdf"
    elif file_path.endswith('.docx'):
        return "microsoft_word"
    elif file_path.endswith(('.xlsx','.xlsm','.xltx','.xltm')):
        return "microsoft_excel"
    elif file_path.endswith(('.jpg', '.jpeg', '.png', '.tiff')):
        return "image_file"    
    elif file_path.endswith(('.txt', '.json')):
        return "text_or_json"
    else:
        # Assume text
        return "text_or_json"

def construct_chain(input_type, args):
    # Use if-elif-else to construct the appropriate chain. In Python 3.10 we could use match statement.
    if input_type == "youtube_url":
        youtube_handler = HandlerFactory.get_handler("YouTubeReaderHandler")
        s3writer_handler = HandlerFactory.get_handler("AmazonS3WriterHandler")
        transcription_handler = HandlerFactory.get_handler("AmazonTranscriptionHandler")
        local_file_writer_handler = HandlerFactory.get_handler("LocalFileWriterHandler")
        
        chain = youtube_handler
        current_handler = youtube_handler.set_next(s3writer_handler).set_next(transcription_handler).set_next(local_file_writer_handler)
    elif input_type == "multimedia_file":
        s3writer_handler = HandlerFactory.get_handler("AmazonS3WriterHandler")
        transcription_handler = HandlerFactory.get_handler("AmazonTranscriptionHandler")
        local_file_writer_handler = HandlerFactory.get_handler("LocalFileWriterHandler")

        chain = s3writer_handler
        current_handler = s3writer_handler.set_next(transcription_handler).set_next(local_file_writer_handler)
    elif input_type == "image_file":
        local_file_reader_handler = HandlerFactory.get_handler("LocalFileReaderHandler")
        textract_handler = HandlerFactory.get_handler("AmazonTextractHandler")

        chain = local_file_reader_handler
        current_handler = local_file_reader_handler.set_next(textract_handler)        
    elif input_type == "pdf":
        pdf_handler = HandlerFactory.get_handler("PDFReaderHandler")

        chain = pdf_handler
        current_handler = pdf_handler 
    elif input_type == "http":
        http_handler = HandlerFactory.get_handler("HTTPHandler")
        http_clean_handler = HandlerFactory.get_handler("HTMLCleanerHandler")
        local_file_writer_handler = HandlerFactory.get_handler("LocalFileWriterHandler")

        chain = http_handler
        current_handler = http_handler.set_next(http_clean_handler).set_next(local_file_writer_handler)
    elif input_type == "text_or_json":
        local_file_reader_handler = HandlerFactory.get_handler("LocalFileReaderHandler")

        chain = local_file_reader_handler
        current_handler = local_file_reader_handler
    elif input_type == "s3":
        s3reader_handler = HandlerFactory.get_handler("AmazonS3ReaderHandler")
        current_handler = chain = s3reader_handler        

    elif input_type == "quip":
        quip_reader_handler = HandlerFactory.get_handler("QuipReaderHandler")
        http_clean_handler = HandlerFactory.get_handler("HTMLCleanerHandler")

        chain = quip_reader_handler
        current_handler = quip_reader_handler.set_next(http_clean_handler)
    elif input_type == "microsoft_word":
        chain = current_handler = HandlerFactory.get_handler("MicrosoftWordReaderHandler")
    elif input_type == "microsoft_excel":
        chain = current_handler = HandlerFactory.get_handler("MicrosoftExcelReaderHandler")

    else:
        # For unsupported types, default to just summarization_handler
        print("Unsupported file type.", input_type)
        sys.exit(1)

    # Add the prompt and bedrock handlers.
    prompt_handler = HandlerFactory.get_handler("PromptHandler")
    bedrock_handler = HandlerFactory.get_handler("AmazonBedrockHandler")    
    current_handler = current_handler.set_next(prompt_handler).set_next(bedrock_handler)
  
    # DataZone Glossary Handler
    dz = HandlerFactory.get_handler("AmazonDataZoneGlossaryWriterHandler")
    current_handler = current_handler.set_next(dz)        
    return chain


def process_file(file_path, args):
    print(f"Processing: {file_path}")
    
    input_type = determine_input_type(file_path)
    handler_chain = construct_chain(input_type, args)

    # Prepare the output filename with the current date and time
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file = f"./downloads/output_{os.path.basename(file_path)}_{current_time}.txt"
    
    
    # Package the request
    request = {
        "type": input_type,
        "path": file_path,
        "prompt_file_name": args.prompt_file_name,
        "text": "",
        "write_file_path": output_file,
        "domain_id": "",
        "project_id": ""
    }

    result = handler_chain.handle(request)
    return result



def main():
 # Initialize the argument parser
    parser = argparse.ArgumentParser(description='Process input files or URLs. Optionally, specify a custom processing chain.')

    # Required positional argument for the file/URL to process
    parser.add_argument('path', type=str, help='The path to the file or URL to be processed.')

    # Optional positional argument for the prompt file name, with a default value
    parser.add_argument('prompt_file_name', nargs='?', default='glossary', help='The name of the prompt file. Defaults to "default_prompt" if not specified.')

  
    # Parse the command-line arguments
    args = parser.parse_args()

    # Handler discovery
    HandlerFactory.discover_handlers()

    if os.path.isdir(args.path):
        max_processes = int(os.getenv('MAX_PARALLEL_PROCESSES', 1))
        with ThreadPoolExecutor(max_workers=max_processes) as executor:
            futures = [executor.submit(process_file, os.path.join(args.path, f), args) for f in os.listdir(args.path) if os.path.isfile(os.path.join(args.path, f))]
            for future in as_completed(futures):
                print(future.result())
    elif os.path.isfile(args.path):
        print(process_file(args.path, args))


if __name__ == "__main__":
    main()