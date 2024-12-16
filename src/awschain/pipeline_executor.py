import yaml
from .handlers.handler_factory import HandlerFactory

class PipelineExecutor:
    @staticmethod
    def load_pipeline(pipeline_path: str):
        try:
            with open(pipeline_path, "r") as file:
                pipeline_config = yaml.safe_load(file)

            return pipeline_config            
        except FileNotFoundError:
            print(f"Error: Pipeline file not found at {pipeline_path}")
        
    def execute(self, pipeline_config: dict, inputs: dict):
        steps = pipeline_config.get("steps", [])
        handler_chain = None
        prev_handler = None

        for step in steps:
            handler_name = step["handler"]
            handler = HandlerFactory.get_handler(handler_name)

            # Configure the handler if needed
            config = step.get("config", {})
            if config and hasattr(handler, "configure"):
                handler.configure(config)

            # Build the chain
            if prev_handler:
                prev_handler.set_next(handler)
            else:
                handler_chain = handler

            prev_handler = handler

        # Execute the chain with the input data
        if handler_chain:
            print(f"Executing the chain with input data: {inputs}")
            return handler_chain.handle(inputs)