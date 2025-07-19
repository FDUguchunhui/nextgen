import os

from openai import OpenAI
from vanna.base import VannaBase
from vanna.chromadb import ChromaDB_VectorStore

class LlamaLLM(VannaBase):

    
    def __init__(self, config=None):
        if config is None:
            raise ValueError(
                "Config must be provided with APIM_SUBSCRIPTION_KEY"
            )

        if "APIM_SUBSCRIPTION_KEY" not in config:
            raise ValueError("config must contain APIM_SUBSCRIPTION_KEY")

        self.client = OpenAI(
            api_key="unused",
            base_url="https://apimd.mdanderson.edu/dig/llm/llama31-70b/v1/",
            default_headers={"Ocp-Apim-Subscription-Key": config["APIM_SUBSCRIPTION_KEY"]},
        )
        self.model = "unused"

    def set_temperature(self, temperature: float) -> None:
        """Set the temperature for text generation."""
        self.temperature = temperature

    def system_message(self, message: str) -> any:
        return {"role": "system", "content": message}

    def user_message(self, message: str) -> any:
        return {"role": "user", "content": message}

    def assistant_message(self, message: str) -> any:
        return {"role": "assistant", "content": message}

    def generate_sql(self, question: str, **kwargs) -> str:
        # Use the super generate_sql
        sql = super().generate_sql(question, **kwargs)

        # Replace "\_" with "_"
        sql = sql.replace("\\_", "_")

        return sql

    def submit_prompt(self, prompt, **kwargs) -> str:
        completion = self.client.chat.completions.create(
            messages=prompt,
            model=self.model,
            temperature=0
        )

        return completion.choices[0].message.content
    

class MyVanna(ChromaDB_VectorStore, LlamaLLM):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        LlamaLLM.__init__(self, config=config)