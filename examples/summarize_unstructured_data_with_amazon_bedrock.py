#!/opt/anaconda3/bin/python
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import json
import os
import sys
from typing import Any
from awschain import HandlerFactory, ConfigLoader
import argparse


# Load config
ConfigLoader.load_config('../config.yaml')

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
    elif file_path.endswith('.pptx'):
        return "microsoft_pp"
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

    elif input_type == "multimedia_file_whisper":
        transcription_handler = HandlerFactory.get_handler("OpenAIWhisperTranscriptionHandler")
        local_file_writer_handler = HandlerFactory.get_handler("LocalFileWriterHandler")

        chain = transcription_handler
        current_handler = transcription_handler.set_next(local_file_writer_handler)        
    elif input_type == "image_file":
        local_file_reader_handler = HandlerFactory.get_handler("LocalFileReaderHandler")
        textract_handler = HandlerFactory.get_handler("AmazonTextractHandler")
        local_file_writer_handler = HandlerFactory.get_handler("LocalFileWriterHandler")
        chain = local_file_reader_handler
        current_handler = local_file_reader_handler.set_next(textract_handler).set_next(local_file_writer_handler)       
    elif input_type == "pdf":
        pdf_handler = HandlerFactory.get_handler("PDFReaderHandler")
        local_file_writer_handler = HandlerFactory.get_handler("LocalFileWriterHandler")

        chain = pdf_handler
        current_handler = pdf_handler.set_next(local_file_writer_handler)

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
        # local_file_reader_handler = HandlerFactory.get_handler("LocalFileReaderHandler")
        current_handler = chain = s3reader_handler        

    elif input_type == "quip":
        quip_reader_handler = HandlerFactory.get_handler("QuipReaderHandler")
        http_clean_handler = HandlerFactory.get_handler("HTMLCleanerHandler")
        local_file_writer_handler = HandlerFactory.get_handler("LocalFileWriterHandler")

        chain = quip_reader_handler
        current_handler = quip_reader_handler.set_next(http_clean_handler).set_next(local_file_writer_handler)
    elif input_type == "microsoft_word":
        msword_handler = HandlerFactory.get_handler("MicrosoftWordReaderHandler")
        local_file_writer_handler = HandlerFactory.get_handler("LocalFileWriterHandler")
        chain = msword_handler
        current_handler = msword_handler.set_next(local_file_writer_handler)
    
    elif input_type == "microsoft_excel":
        xls_hanlder = HandlerFactory.get_handler("MicrosoftExcelReaderHandler")
        local_file_writer_handler = HandlerFactory.get_handler("LocalFileWriterHandler")
        chain = xls_hanlder
        current_handler = xls_hanlder.set_next(local_file_writer_handler)
    elif input_type == "microsoft_pp":
        pp_handler = HandlerFactory.get_handler("MicrosoftPowerPointReaderHandler")
        local_file_writer_handler = HandlerFactory.get_handler("LocalFileWriterHandler")
        chain = pp_handler
        current_handler = pp_handler.set_next(local_file_writer_handler)
    elif input_type == "custom":
        return construct_custom_chain() # for testing only
            # construct and return a custom chain.    
    else:
        # For unsupported types, default to just summarization_handler
        print("Unsupported file type.", input_type)
        sys.exit(1)
    
    # Anonymize data?
    anonymize = args.anonymize in (True, 'true', '1')
    if anonymize: 
        anonymize_handler = HandlerFactory.get_handler("AmazonComprehendPIITokenizeHandler")
        current_handler = current_handler.set_next(anonymize_handler)

    # Add the prompt and bedrock handlers.
    prompt_handler = HandlerFactory.get_handler("PromptHandler")
    bedrock_handler = HandlerFactory.get_handler("AmazonBedrockHandler")    
        
    # Determinate when / if we need to call summarization or Chat and in what order.
    
    if args.chat and args.chat != None: 
        chat_handler = HandlerFactory.get_handler("AmazonBedrockChatHandler")
        print("Enable chat", args)
        if args.chat == 'sum_first':
            current_handler = current_handler.set_next(prompt_handler).set_next(bedrock_handler).set_next(chat_handler)

        elif args.chat == 'chat_only': 
            current_handler = current_handler.set_next(chat_handler)
            
        else: 
            current_handler = current_handler.set_next(chat_handler)
            current_handler = current_handler.set_next(prompt_handler).set_next(bedrock_handler)
    else: 
        current_handler = current_handler.set_next(prompt_handler).set_next(bedrock_handler)
    
    # Finally, if we have tokenized the content, let's untokenize
    if anonymize:
        unanonymize_handler = HandlerFactory.get_handler("AmazonComprehendPIIUntokenizeHandler")
        current_handler = current_handler.set_next(unanonymize_handler)

    # Copy to clipboard?
    clipboard = os.getenv('CLIPBOARD_COPY', 'false').lower() in ('true', '1', 't')
    if clipboard:         
        clipboard_handler = HandlerFactory.get_handler("ClipboardWriterHandler")
        current_handler = current_handler.set_next(clipboard_handler)
        print("\n\n  ================================================\n   The summary will be copied to your clipboard.\n  ================================================\n")    
        
    return chain

def construct_custom_chain():
    # Get creative...
    # youtube_handler = HandlerFactory.get_handler("YouTubeReaderHandler")
    # amazon_transcribe_handler = HandlerFactory.get_handler("AmazonTranscriptionHandler")
    
    local_file_reader_handler = HandlerFactory.get_handler("LocalFileReaderHandler")
    anonymize_handler = HandlerFactory.get_handler("AmazonComprehendPIITokenizeHandler")
    local_file_writer_handler = HandlerFactory.get_handler("LocalFileWriterHandler")
    # pdf_handler = HandlerFactory.get_handler("PDFReaderHandler")
    # pii_handler = HandlerFactory.get_handler("AmazonComprehendPIIClassifierHandler")
    prompt_handler = HandlerFactory.get_handler("PromptHandler")
    # amazon_bedrock_handler = HandlerFactory.get_handler("AmazonBedrockHandler")

    # amazon_s3_writer_handler = HandlerFactory.get_handler("AmazonS3WriterHandler")
    # amazon_s3_reader_handler = HandlerFactory.get_handler("AmazonS3ReaderHandler")
    # http_handler = HandlerFactory.get_handler("HTTPHandler")
    # textract_handler = HandlerFactory.get_handler("AmazonTextractHandler")
    # anonymize_handler = HandlerFactory.get_handler("AnonymizeHandler")
    # quip_reader_handler = HandlerFactory.get_handler("QuipReaderHandler")
    # quip_writer_handler = HandlerFactory.get_handler("QuipWriterHandler")
    # http_clean_handler = HandlerFactory.get_handler("HTMLCleanerHandler")
    # ms = HandlerFactory.get_handler("MicrosoftWordReaderHandler")
    # chat = HandlerFactory.get_handler("AmazonBedrockChatHandler")

    # dz = HandlerFactory.get_handler("AmazonDataZoneGlossaryWriterHandler")
    # tokenize = HandlerFactory.get_handler("AmazonComprehendPIITokenizeHandler")
    # untokenize = HandlerFactory.get_handler("AmazonComprehendPIIUntokenizeHandler")
    # insights = HandlerFactory.get_handler("AmazonComprehendInsightsHandler")
    # printh = HandlerFactory.get_handler("PrintContextHandler")
    # download = HandlerFactory.get_handler("RemoteFileDownloaderHandler")
    # chain = pdf_handler
    # pdf_handler.set_next(quip_writer_handler)

    # s3writer_handler = HandlerFactory.get_handler("AmazonS3WriterHandler")
    # transcription_handler = HandlerFactory.get_handler("AmazonTranscriptionHandler")
    # local_file_writer_handler = HandlerFactory.get_handler("LocalFileWriterHandler")

    # web_crawler = HandlerFactory.get_handler("WebCrawlerReaderHandler")

    # llama = HandlerFactory.get_handler("LocalLlamaHandler")
    # chain = local_file_reader_handler
    # local_file_reader_handler.set_next(prompt_handler).set_next(llama)

    # s3writer_handler.set_next(transcription_handler).set_next(local_file_writer_handler)


    #Unstructured data 
    # chain = HandlerFactory.get_handler("QuipReaderHandler")
    # insights = HandlerFactory.get_handler("AmazonComprehendInsightsHandler")

    # email = HandlerFactory.get_handler("EmailReaderHandler")
    # chain = email

    #DataZone use case
    # chain = ms
    # ms.set_next(prompt_handler).set_next(amazon_bedrock_handler).set_next(dz).set_next(local_file_writer_handler)

    # ms.set_next(tokenize).set_next(untokenize)
    

    # local_file_reader_handler.set_.set_next(local_file_writer_handler)
    
    # http_handler.set_next(quip_writer_handler)

    # amazon_s3_writer_handler.set_next(amazon_transcribe_handler)#.set_next(prompt_handler).set_next(amazon_bedrock_handler)
    # Read Youtube Video >> Save Audio in Amazon S3 >> Extract text from speach (Amazon Transcribe) >> Construct a prompt >> Summarize using Amazon Bedrock.
    
    # youtube_handler.set_next(amazon_s3_writer_handler).set_next(amazon_transcribe_handler).set_next(prompt_handler).set_next(anonymize_handler).set_next(amazon_bedrock_handler)
    # s3reader_handler.set_next(local_file_writer_handler)

    transcription_handler = HandlerFactory.get_handler("OpenAIWhisperTranscriptionHandler")
    local_file_writer_handler = HandlerFactory.get_handler("LocalFileWriterHandler")

    chain = transcription_handler
    current_handler = transcription_handler.set_next(local_file_writer_handler)   
         
    return chain

def process_file(file_path, args):
    print(f"Processing: {file_path}")
    if args.custom:
        input_type = "custom"
    else:
        input_type = determine_input_type(file_path)
    
    handler_chain = construct_chain(input_type, args)

    # Prepare the output filename with the current date and time
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    local_dir = os.getenv('DIR_STORAGE', './downloads')
    output_file = f"{local_dir}/output_{os.path.basename(file_path)}_{current_time}.txt"
    
    
    request = {
        "type": input_type,
        "path": file_path,
        "prompt_file_name": args.prompt_file_name,
        "text": "",
        "write_file_path": output_file,
        "extract_media": True
    }

    result = handler_chain.handle(request)
    return result


def main():
 # Initialize the argument parser
    parser = argparse.ArgumentParser(description='Process input files or URLs. Optionally, specify a custom processing chain.')

    # Required positional argument for the file/URL to process
    parser.add_argument('path', type=str, help='The path to the file, folder or URL to be processed.')

    # Optional positional argument for the prompt file name, with a default value
    parser.add_argument('prompt_file_name', nargs='?', default='default_prompt', help='The name of the prompt file. Defaults to "default_prompt" if not specified.')

    # Optional flag to specify the use of a interactive chat handler
    parser.add_argument("--chat", type=str, default=None, choices=[None, 'sum_first', 'chat_first', 'chat_only'],  help="Choose 'sum_first', 'chat_first' to summarize before chat or direct chat interaction with your original text. Select 'chat_only' if you only want to query your original text")

    # Optional flag to turn off anonymization
    parser.add_argument("--anonymize", type=str, default=True, help="Anonymize customer names before sending to the model. By default this is set to true.")

    # Optional flag to specify the use of a custom chain
    parser.add_argument('--custom', action='store_true', help='Flag to use a custom processing chain instead of the default based on file type.')

    # Parse the command-line arguments
    args = parser.parse_args()

    # Handler discovery
    HandlerFactory.discover_handlers()
 
    if os.path.isdir(args.path):
        max_processes = int(os.getenv('MAX_PARALLEL_PROCESSES', 1))
        with ThreadPoolExecutor(max_workers=max_processes) as executor:
            futures = [executor.submit(process_file, os.path.join(args.path, f), args) for f in os.listdir(args.path) if os.path.isfile(os.path.join(args.path, f))]
            for future in as_completed(futures):
                result = future.result()
    else:
        result = process_file(args.path, args)

    if result.get("text", None):
        print(result.get("text"))
    else:
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()