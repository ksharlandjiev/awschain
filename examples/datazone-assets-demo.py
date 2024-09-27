#!/opt/anaconda3/bin/python
import os
import sys
import json
import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from awschain import HandlerFactory, ConfigLoader
from utils.helper import determine_input_type, repair_json

# Load config
ConfigLoader.load_config()

def construct_chain(input_type, args):
    """Constructs the appropriate handler chain based on the input type."""

    local_file_writer_handler = HandlerFactory.get_handler("LocalFileWriterHandler")
        
    if input_type == "youtube_url":
        chain = HandlerFactory.get_handler("YouTubeReaderHandler")
        chain.set_next(
            HandlerFactory.get_handler("AmazonS3WriterHandler")
        ).set_next(
            HandlerFactory.get_handler("AmazonTranscriptionHandler")
        ).set_next(local_file_writer_handler)
    elif input_type == "multimedia_file":
        chain = HandlerFactory.get_handler("AmazonS3WriterHandler")
        chain.set_next(
            HandlerFactory.get_handler("AmazonTranscriptionHandler")
        ).set_next(local_file_writer_handler)
    elif input_type == "image_file":
        chain = HandlerFactory.get_handler("LocalFileReaderHandler")
        chain.set_next(
            HandlerFactory.get_handler("AmazonTextractHandler")
        ).set_next(local_file_writer_handler)
    elif input_type == "pdf":
        chain = HandlerFactory.get_handler("PDFReaderHandler")
        chain.set_next(local_file_writer_handler)
    elif input_type == "http":
        chain = HandlerFactory.get_handler("HTTPHandler")
        chain.set_next(
            HandlerFactory.get_handler("HTMLCleanerHandler")
        ).set_next(local_file_writer_handler)
    elif input_type == "text_or_json":
        chain = HandlerFactory.get_handler("LocalFileReaderHandler")
    elif input_type == "s3":
        chain = HandlerFactory.get_handler("AmazonS3ReaderHandler")
        chain.set_next(local_file_writer_handler)
    elif input_type == "quip":
        chain = HandlerFactory.get_handler("QuipReaderHandler")
        chain.set_next(
            HandlerFactory.get_handler("HTMLCleanerHandler")
        ).set_next(local_file_writer_handler)
    elif input_type == "microsoft_word":
        chain = HandlerFactory.get_handler("MicrosoftWordReaderHandler")
        chain.set_next(local_file_writer_handler)
    elif input_type == "microsoft_excel":
        chain = HandlerFactory.get_handler("MicrosoftExcelReaderHandler")
        chain.set_next(local_file_writer_handler)
    elif input_type == "microsoft_pp":
        chain = HandlerFactory.get_handler("MicrosoftPowerPointReaderHandler")
        chain.set_next(local_file_writer_handler)
    else:
        print("Unsupported file type.", input_type)
        sys.exit(1)
        
    return chain

def process_file(file_path, args):
    """Processes a single file or URL based on its type."""
    print(f"Processing: {file_path}")

    bucket = os.getenv('S3_DATALAKE_BUCKET', None)
    if not bucket:
        raise Exception("S3_DATALAKE_BUCKET environment variable not set.")
    
    prefix = os.getenv('S3_DATALAKE_PREFIX', "")
    meta_prefix = os.getenv('S3_DATALAKE_METADATA_PREFIX', "")

    # Determine input type and construct handler chain
    input_type = determine_input_type(file_path)
    handler_chain = construct_chain(input_type, args)

    # Prepare the output filename with the current date and time
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file = f"./downloads/output_{os.path.basename(file_path)}_{current_time}.txt"
    file_name = os.path.basename(file_path)
    transcript_file_name = f"{file_name}_transcript.txt"
    
    request = {
        "type": input_type,
        "path": file_path,
        "text": "",
        "prompt_file_name": 'meta',
        "write_file_path": output_file,
        "extract_media": False  # Enable media extraction for image and video files
    }

    # Process the file through the handler chain
    result = handler_chain.handle(request)
    
    # Saving transcription for later upload.
    transcript_text = ""
    if result.get("text") and result.get("text") != "":
        transcript_text = result.get("text")

    # Get metadata from the result
    media_metadata = result.get("metadata", {})

    # Copy extracted text to S3
    amazon_s3_writer_handler = HandlerFactory.get_handler("AmazonS3WriterHandler")

    # Detect and classify PII, Summarize with Bedrock
    anonymize_handler = HandlerFactory.get_handler("AmazonComprehendPIITokenizeHandler")
    prompt_handler = HandlerFactory.get_handler("PromptHandler")
    bedrock_handler = HandlerFactory.get_handler("AmazonBedrockHandler")
    unanonymize_handler = HandlerFactory.get_handler("AmazonComprehendPIIUntokenizeHandler")
    
    chain = HandlerFactory.get_handler("AmazonComprehendPIIClassifierHandler")

    chain.set_next(anonymize_handler)\
        .set_next(prompt_handler)\
        .set_next(bedrock_handler)\
        .set_next(unanonymize_handler)
    
    result = chain.handle(result)
    bedrock_text = result.get("text")
    is_broken = False
    try:
        bedrock_metadata = json.loads(bedrock_text)
    except json.JSONDecodeError as e:
        print("Failed to parse JSON:", e)
        print("Broken Json: ", bedrock_text)
        print("Trying to repair JSON...")
        repaired_json = repair_json(bedrock_text)
        try:
            bedrock_metadata = json.loads(repaired_json)
        except json.JSONDecodeError as e:
            is_broken = True
            bedrock_metadata = {}

    if is_broken:
        category = "broken"
    else:
        category = bedrock_metadata.get("category", None)

        if category:
            prefix = f"{prefix}/category={category}"  

        original_file_s3 = f"s3://{bucket}/{prefix}/{file_name}"
        transcript_file_s3 = f"s3://{bucket}/{prefix}/{transcript_file_name}"
        
        # Copy data to S3
        if result.get("type") in ["http", "quip", "s3"]: # Remote assets
            title = bedrock_metadata.get("title")
            metadata_form_original_file = file_path
            original_file_s3 = f"s3://{bucket}/{prefix}/{title}.txt"
            transcript_file_s3 = f"s3://{bucket}/{prefix}/{title}_transcript.txt"
            file_path = result.get("write_file_path")
        elif result.get("type") == "youtube_url":
            title = bedrock_metadata.get("title")
            metadata_form_original_file = file_path
            original_file_s3 = result.get("path")
            transcript_file_s3 = f"s3://{bucket}/{prefix}/{title}_transcript.txt"
            file_path = result.get("write_file_path")
        else:  # local assets
            output_file = file_path 
            metadata_form_original_file = original_file_s3

        # print(f"Result: {result}")
        # print(f"Metadata: {bedrock_metadata}")
        
        # Write original data in S3.
        data_request = {
            "type": input_type,
            "path": output_file,
            "write_file_path": original_file_s3,         
        }          
        amazon_s3_writer_handler.handle(data_request)

        # Write transcript to S3
        request = {
            "text": transcript_text,
            "write_file_path": transcript_file_s3
        }
        amazon_s3_writer_handler.handle(request)

        # Merge metadata
        merged_metadata = {
            "file_type": input_type,
            "original_file": metadata_form_original_file,
            "is_pii": result.get("is_pii", False),
            "detected_pii": result.get("detected_pii", []),
            "transcript_file": transcript_file_s3,
            "media_files": media_metadata.get(file_path, {}).get("media_files", []),
            **bedrock_metadata
        }
        
        # Write the merged metadata to S3
        request = {
            "text": json.dumps(merged_metadata),
            "write_file_path": f"s3://{bucket}/{meta_prefix}/metadata_{datetime.now()}.json"
        }
        amazon_s3_writer_handler.handle(request)
    
        #Write asset to Datazone     
        dz = HandlerFactory.get_handler("AmazonDataZoneAssetWriterHandler")
        dz.handle(merged_metadata)
        
        # Chain for image metadata enhancement
        # if not is_broken:
        #     rekognition_handler = HandlerFactory.get_handler("AmazonRekognitionHandler")
        #     rekognition_handler.handle(result)

        return merged_metadata

def main():
    # Initialize the argument parser
    parser = argparse.ArgumentParser(description='Process input files or URLs. Optionally, specify a custom processing chain.')

    # Required positional argument for the file/URL to process
    parser.add_argument('csv_path', type=str, help='The path to the CSV file containing the list of files or URLs to be processed.')
    
    # Optional argument to specify the output file for results
    parser.add_argument('--output-file', type=str, help='The file to save the output results.')

    # Parse the command-line arguments
    args = parser.parse_args()

    # Handler discovery
    HandlerFactory.discover_handlers()
    results = []

    def process_files_in_parallel(file_paths, args):
        """Process files in parallel with a limit on the number of parallel processes."""
        
        # Load MAX_PARALLEL_PROCESSES from environment variables
        max_parallel_processes = int(os.getenv('MAX_PARALLEL_PROCESSES', 1))
        results = []
        with ThreadPoolExecutor(max_workers=max_parallel_processes) as executor:
            futures = [executor.submit(process_file, file_path, args) for file_path in file_paths]
            for future in as_completed(futures):
                results.append(future.result())
        return results

    # Read CSV file and process files in parallel
    with open(args.csv_path, newline='') as csvfile:
        file_paths = [row.strip() for row in csvfile if row.strip()]
        process_files_in_parallel(file_paths, args)

    # # Print results
    results_json = json.dumps(results, indent=4)
    # print(results_json)
    
    # Save results to file if specified
    if args.output_file:
        with open(args.output_file, 'w') as output_file:
            output_file.write(results_json)

if __name__ == "__main__":
    main()
