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
        self.conversation_history = []  # Initialize conversation history

    def chat(self, message: str) -> str:
        self.conversation_history.append({"role": "user", "content": message})

        params = {
            "messages": self.conversation_history,
            "temperature": self._invocation_params.get("temperature", 0),
            **self._invocation_params
        }
        try:
            response = self.client.create(**params)
            reply = response.choices[0].message.content
            self.conversation_history.append({"role": "assistant", "content": reply})
            return reply
        except Exception as e:
            logging.error(f"Error during chat completion: {e}")
            return "An error occurred while processing your request."