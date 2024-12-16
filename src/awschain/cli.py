import argparse
import json
from .pipeline_executor import PipelineExecutor

def main():
    parser = argparse.ArgumentParser(description="Execute preconfigured awschain pipelines.")
    parser.add_argument(
        "--pipeline",
        required=True,
        help="Path to the pipeline YAML configuration file."
    )
    parser.add_argument(
        "--inputs",
        required=True,
        help="JSON string with input data for the pipeline."
    )

    args = parser.parse_args()

    # Load pipeline configuration
    executor = PipelineExecutor()
    pipeline_config = executor.load_pipeline(args.pipeline)

    # Parse input data
    inputs = json.loads(args.inputs)

    # Execute the pipeline
    result = executor.execute(pipeline_config, inputs)
    print(result)