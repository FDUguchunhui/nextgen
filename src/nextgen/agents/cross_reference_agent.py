
import os
import re
import math
import json
from typing import List, Dict
from openai import OpenAI
import openai
import chromadb
from nextgen.agents.agents import Agent
import pandas as pd
from IPython.display import Markdown

class CrossReferenceAgent(Agent):

    name: str = "Analysis Agent"
    color: str = '\033[32m'

    def __init__(self, client="llama"):
        super().__init__()
        
        # Instantiate the client. Make sure the client points to the self-hosted LLM.
        self.client = None
        if client == "MDA":
            self.client = OpenAI(
                api_key="unused",
                base_url="https://apimd.mdanderson.edu/dig/llm/llama31-70b/v1/",
                default_headers={"Ocp-Apim-Subscription-Key": os.environ["APIM_SUBSCRIPTION_KEY"]},
            )

    
    def make_message(self, question: str, proteins: List[str]) -> str:
        """
        Send a message to the LLM.
        """
        system_message = f'''
        You are a cancer biology expert. You are given a question and a list of proteins.
        You need to cross-check the proteins with the online literature. 
        You should list the supporting evidence for each protein for the question.
        For proteins without existing supporting literature, you should mention that and give possible reasons why 
        it is possible that the proteins is still important for the question.
        You should list the validated proteins first and then the potential proteins.
        You should ouput the results in markdown format.
        '''
        user_prompt = f'''
        Question: {question},
        Proteins: {proteins}
        '''

        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt}
        ]


    def analyze(self, question: str, proteins: List[str]) -> str:

        # 3. Create message for LLM
        messages = self.make_message(question, proteins)
        
        # 4. Get LLM response
        if self.client is None:
            completion = openai.ChatCompletion.create(
            model="gpt-4o-search-preview",
            messages=messages,
            web_search_options={},
            max_tokens=1000,
            api_key=os.environ["OPENAI_API_KEY"])
        else:
            completion = self.client.chat.completions.create(
            messages=messages,
            model="unused"
            )


        
        return completion.choices[0].message.content


if __name__ == "__main__":
    question = "What are the proteins that are important for breast cancer?"
    proteins = ['P02649', 'P19823', 'P0C0L5', 'P08571', 'P01031', 'P01024', 'P80108', 'P06727', 'P00450', 'P08603', 'P10909', 'P10909-2', 'P10909-4', 'P10909-5', 'P10909-6', 'P35542', 'P02749', 'P02656', 'P01008', 'P02647']

    cross_reference_agent = CrossReferenceAgent(client="MDA")
    result = cross_reference_agent.analyze(question, proteins)
    print(result)
    # print(Markdown())



