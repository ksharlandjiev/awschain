"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 
Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so.
 
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import sys
import json
import boto3
import pandas as pd
from typing import Any, Dict
from botocore.config import Config
from botocore.exceptions import ClientError
from awschain import HandlerFactory, ConfigLoader
from awschain.handlers.handler_factory import HandlerFactory


# Configure XLS Column names that contains the Glossary Name, Glossary Term and description.
COLUMN_NAME_GLOSSARY = "Datasets"
COLUMN_NAME_GLOSSARY_TERM = "Tables"
COLUMN_NAME_GLOSSARY_SHORT_DESCRIPTION = "Description/Notes"

# Load config
ConfigLoader.load_config()


def handle(self, request: dict) -> dict:
    my_config = Config(region_name=AWS_REGION_ID)
    self.datazone_client = boto3.client("datazone", config=my_config)

    print("Processing DataZone glossaries...")

    if not self.validate_glossary_structure(request.get("text")):
        raise ValueError("The glossary structure is invalid.")

    domain_id = request.get("domain_id") or input("Enter the DataZone Domain ID: ")
    project_id = request.get("project_id") or input("Enter the DataZone Project ID: ")

    self.process_glossary(request["text"], domain_id, project_id)


def validate_glossary_structure(self, glossary_text: str) -> bool:
    try:
        glossary = json.loads(glossary_text)
        return isinstance(glossary, dict) and all(
            isinstance(terms, list) and all(
                isinstance(term, dict) and "name" in term and "shortDescription" in term for term in terms
            ) for category, terms in glossary.items()
        )
    except json.JSONDecodeError:
        return False

def process_glossary(self, glossary_text: str, domain_id: str, project_id: str):
    glossary = json.loads(glossary_text)
    for category, terms in glossary.items():
        glossary_id = self.create_or_get_glossary(category, domain_id, project_id)
        for term in terms:
            self.add_term_to_glossary(domain_id, glossary_id, term)

def create_or_get_glossary(self, category_name: str, domain_id: str, project_id: str) -> str:
    try:
        # Search for an existing glossary using the Search API
        response = self.datazone_client.search(
            domainIdentifier=domain_id,
            owningProjectIdentifier=project_id,
            searchScope='GLOSSARY',
            searchText=category_name,
            maxResults=1,
            filters={
                'filter': {
                    'attribute': 'name',
                    'value': category_name
                }
            }
        )
        # Check if the glossary exists
        if response['totalMatchCount'] > 0:
            glossary_id = response['items'][0]['glossaryItem']['id']
            print(f"Found existing glossary for: {category_name} with ID: {glossary_id}")
            return glossary_id
    except ClientError as error:
        print(f"Error searching for glossary: {error}")
        raise

    # If no existing glossary found, or searching failed, create a new one
    print(f"Creating new glossary for: {category_name}")
    try:
        create_response = self.datazone_client.create_glossary(
            domainIdentifier=domain_id,
            owningProjectIdentifier=project_id,
            name=category_name,
            description=f"Glossary for {category_name}",
            status='ENABLED',
        )
        return create_response["id"]
    except ClientError as error:
        print(f"Error creating glossary: {error}")
        raise

def add_term_to_glossary(self, domain_id, glossary_id: str, term: Dict[str, Any]):
    print(f"Creating new glossary term: {term['name']}")

    try:
        # Ensure shortDescription is valid and cleaned up
        short_description = term['shortDescription']
        if not short_description:
            short_description = ""  # Replace NaN with empty string

        # Remove unwanted symbols like _x000D_\n
        short_description = short_description.replace("_x000D_", "").replace("\n", " ").strip()

        self.datazone_client.create_glossary_term(
            domainIdentifier=domain_id,
            glossaryIdentifier=glossary_id,
            name=term['name'],
            shortDescription=short_description,
            status='ENABLED'            
        )
    except ClientError as error:
        print(f"Error adding term '{term['name']}' to glossary: {error}")

def read_xlsx_file(file_path: str) -> dict:
    """
    Reads the given XLSX file and returns a dictionary suitable for the glossary writer.
    The XLSX file must have at least three columns as defined above.
    """
    try:
        df = pd.read_excel(file_path)

        if not all(col in df.columns for col in [COLUMN_NAME_GLOSSARY, COLUMN_NAME_GLOSSARY_TERM, COLUMN_NAME_GLOSSARY_SHORT_DESCRIPTION]):
            raise ValueError(f"Columns are missing: {df.columns}")

        # Group the dataframe by category and create the dictionary
        glossary = {}
        for category, group in df.groupby(COLUMN_NAME_GLOSSARY):
            terms = group[[COLUMN_NAME_GLOSSARY_TERM, COLUMN_NAME_GLOSSARY_SHORT_DESCRIPTION]].to_dict(orient='records')

            # Ensure to handle NaN and replace it with an empty string
            glossary[category] = [
                {
                    'name': term[COLUMN_NAME_GLOSSARY_TERM], 
                    'shortDescription': "" if pd.isna(term[COLUMN_NAME_GLOSSARY_SHORT_DESCRIPTION]) else str(term[COLUMN_NAME_GLOSSARY_SHORT_DESCRIPTION]).replace("_x000D_", "").replace("\n", " ").strip()
                } 
                for term in terms
            ]

        return glossary

    except Exception as e:
        print(f"Error reading XLSX file: {e}")
        sys.exit(1)


def convert_to_json(glossary_data: dict) -> str:
    """
    Converts the glossary data to a JSON formatted string.
    """
    return json.dumps(glossary_data, indent=2)


def main(file_path: str, domain_id: str = None, project_id: str = None):
    """
    Main function to read the XLSX file, convert it to the JSON format,
    and invoke the glossary writer handler to write the glossaries.
    """
    # Read and convert XLSX data to glossary structure
    glossary_data = read_xlsx_file(file_path)
    glossary_json = convert_to_json(glossary_data)

    # Prepare the request dictionary for the handler
    request = {
        "text": glossary_json,
        "domain_id": domain_id,
        "project_id": project_id
    }

    # Invoke the handler to process the glossary data
    handler = HandlerFactory.get_handler("AmazonDataZoneGlossaryWriterHandler")
    try:
        handler.handle(request)
        print("Glossary writing process completed successfully.")
    except Exception as e:
        print(f"An error occurred during glossary writing: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script_name.py <path_to_xlsx> [domain_id] [project_id]")
        sys.exit(1)

    file_path = sys.argv[1]
    domain_id = sys.argv[2] if len(sys.argv) > 2 else None
    project_id = sys.argv[3] if len(sys.argv) > 3 else None

    main(file_path, domain_id, project_id)