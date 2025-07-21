from openai import OpenAI
import os
import logging

class MDAndersonLLM():
    def __init__(self, **kwargs):
        """Initialize the LLM client with APIM subscription key and optional parameters."""
        self.client = OpenAI(
            api_key="unused",
            base_url="https://apimd.mdanderson.edu/dig/llm/llama31-70b/v1/",
            default_headers={"Ocp-Apim-Subscription-Key": os.environ.get("APIM_SUBSCRIPTION_KEY", "")}
        ).chat.completions

        self._invocation_params = kwargs

    def chat(self, message: str) -> str:

        params = {
            "temperature": self._invocation_params.get("temperature", 0),
            "model": "llama31-70b",
            **self._invocation_params
        }
        messages = [{"role": "user", "content": message}]
        try:
            response = self.client.create(messages=messages, **params)
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"Error during chat completion: {e}")
            return "An error occurred while processing your request."

if __name__ == "__main__":
    llm = MDAndersonLLM()
    print(llm.chat('Hello, how are you?'))