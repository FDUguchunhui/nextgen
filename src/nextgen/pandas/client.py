from __future__ import annotations
from typing import TYPE_CHECKING
import os
from openai import OpenAI
from pandasai.helpers.memory import Memory
from pandasai.prompts.base import BasePrompt
from pandasai.llm.base import LLM

if TYPE_CHECKING:
    from pandasai.pipelines.pipeline_context import PipelineContext

class MDAndersonLLM(LLM):
    def __init__(self, model: str = "unused", **kwargs):
        """Initialize the LLM client with APIM subscription key."""
        self.model = model
        self.client = OpenAI(
            api_key="unused",
            base_url="https://apimd.mdanderson.edu/dig/llm/llama31-70b/v1/",
            default_headers={"Ocp-Apim-Subscription-Key": os.environ["APIM_SUBSCRIPTION_KEY"]}
        ).chat.completions
        self._invocation_params = kwargs

    def chat_completion(self, value: str, memory: Memory) -> str:
        """Execute chat completion with the given value and memory."""
        messages = memory.to_openai_messages() if memory else []
        
        # adding current prompt as latest query message
        messages.append({
            "role": "user",
            "content": value,
        })

        params = {
            "model": self.model,
            "messages": messages,
            "temperature": 0,
            **self._invocation_params
        }
        response = self.client.create(**params)
        
        return response.choices[0].message.content

    def call(self, instruction: BasePrompt, context: PipelineContext = None) -> str:
        """Call the LLM with the given instruction and context."""
        self.last_prompt = instruction.to_string()
        memory = context.memory if context else None
        return self.chat_completion(self.last_prompt, memory)

    @property
    def type(self) -> str:
        """Return type of LLM."""
        return "md-anderson"

if __name__ == "__main__":
    llm = MDAndersonLLM()
    print(llm.call("What is the capital of France?"))
