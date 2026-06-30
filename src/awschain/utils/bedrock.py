# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

# Python Built-Ins:
import json
import os
from jsonpath_ng import parse

# External Dependencies:
import boto3
from botocore.client import Config

def invoke_model(prompt_text, config):
    """
    Invokes an Amazon Bedrock model with a JSON-based prompt configuration.
    """

    try:
        boto3_config = Config(connect_timeout=900)
        boto3_bedrock = boto3.client(
            service_name="bedrock-runtime",
            region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
            config=boto3_config
        )
    except Exception as e:
        print(f"Failed to create Bedrock client: {e}")
        raise e

    body = json.loads(os.environ.get("AMAZON_BEDROCK_MODEL_PROPS", config.get("model_props", '{}')))
    prompt_template = os.environ.get("AMAZON_BEDROCK_PROMPT_TEMPLATE", config.get("prompt_template", ""))
    prompt_var = os.environ.get("AMAZON_BEDROCK_PROMPT_INPUT_VAR", config.get("prompt_input_var", ""))
    output_json_path = os.environ.get("AMAZON_BEDROCK_OUTPUT_JSONPATH", config.get("output_jsonpath", "$"))

    # Format the prompt.
    formatted_prompt = prompt_template.format(prompt_text=prompt_text)

    # Apply JSONPath to find the correct location in the JSON structure.
    jsonpath_expr = parse(prompt_var)

    found = False
    for match in jsonpath_expr.find(body):
        if isinstance(match.value, list) and len(match.value) > 0:
            # If the matched value is a list, assume we need to update the first item.
            if isinstance(match.value[0], dict) and "text" in match.value[0]:
                match.value[0]["text"] = formatted_prompt
                found = True
            else:
                print(f"Unexpected list structure at {prompt_var}. Expected dict with 'text' key.")
        elif isinstance(match.value, str):
            match.context.value[match.path.fields[0]] = formatted_prompt
            found = True
        elif isinstance(match.value, dict):
            # If it's a dictionary, replace it entirely
            match.context.value[match.path.fields[0]] = formatted_prompt
            found = True
        else:
            print(f"Unexpected match type at {prompt_var}: {type(match.value)}")

    if not found:
        print(f"Warning: JSONPath {prompt_var} did not match any existing fields.")

    # print(f"Updated Body: {json.dumps(body, indent=2)}")

    body = json.dumps(body)
    modelId = os.environ.get("AMAZON_BEDROCK_MODEL_ID", config.get("model_id", "amazon.titan-text-express-v1"))

    try:
        response = boto3_bedrock.invoke_model(
            body=body,
            modelId=modelId,
            accept="application/json",
            contentType="application/json"
        )
        resp = response.get("body").read()

        response_body = json.loads(resp)

        # Extract data using the configured JSONPath
        jsonpath_expression = parse(output_json_path)
        try:
            result = jsonpath_expression.find(response_body)
            if result and result[0].value:
                return result[0].value
        except Exception:
            print(f"Failed to apply JSONPath: {output_json_path}, returning the whole body")
            return response_body

    except Exception as e:
        print(f"Failed to invoke model: {e}")
        raise e