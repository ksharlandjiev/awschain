from handlers.abstract_handler import AbstractHandler
from llama_cpp.llama import Llama, LlamaGrammar
import json

class LocalLlamaHandler(AbstractHandler):
    def handle(self, request: dict) -> dict:
        model_path = request.get("model_path", "/Users/awskamen/SourceCode/hugging_face/llama.cpp/models/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf")
        json_schema_output = request.get("json_schema_output", None)

        print(f"Invoking local LLM model with ID: {model_path}")

        # Load the Llama model
        llama = Llama(model_path, verbose=False, n_ctx=631)

        text = request.get("text", "")
        print(f"Processing text: {text}")

        # Optionally apply JSON schema
        grammar = None
        if json_schema_output:
            print("Applying JSON schema for structured output.")
            grammar = LlamaGrammar.from_json_schema(json_schema_output)

        response = self.invoke_llm(llama, text, grammar)

        request.update({"text": response})
        return super().handle(request)

    def invoke_llm(self, llama, text: str, grammar: LlamaGrammar = None) -> str:
        try:
            response = llama(text, grammar=grammar, max_tokens=-1)
            result = json.loads(response['choices'][0]['text'])
            formatted_result = json.dumps(result, indent=4)
            print("Model response:", formatted_result)
            return formatted_result
        except Exception as e:
            print("An error occurred during LLM invocation:", e)
            raise e

