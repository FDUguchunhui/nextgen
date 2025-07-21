
import os
import re
from typing import List, Dict
from openai import OpenAI
from nextgen.agents.agents import Agent
import pandas as pd
import ast
import re

class AnalysisAgent(Agent):

    name: str = "Analysis Agent"
    color: str = '\033[32m'

    def __init__(self, model: str = "md_anderson"):
        super().__init__()
        
        # Instantiate the client. Make sure the client points to the self-hosted LLM.
        if model == "md_anderson":
            self.client = OpenAI(
                api_key="unused",
                base_url="https://apimd.mdanderson.edu/dig/llm/llama31-70b/v1/",
                default_headers={"Ocp-Apim-Subscription-Key": os.environ["APIM_SUBSCRIPTION_KEY"]},
            )
        elif model == "openai":
            self.client = OpenAI(
                api_key=os.environ["OPENAI_API_KEY"],
                base_url="https://api.openai.com/v1",
            )
        else:
            raise ValueError(f"Invalid model: {model}")

    
    def make_message(self, question: str, sql: str, data) -> str:
        """
        Send a message to the LLM.
        """
        system_message = f'''
        You are a data analysis expert. You are given a question and a corresponding dataset retrieved using the following SQL query:
        "{sql}"

        Your task is to extract a list of proteins that answer the question, based strictly on the data.
        You should give as comprehensive answer as possible to the question.

        ✅ Output requirements:
        - Only output valid Python code.
        - The output should look like: `['P12345', 'P23456', ...]`
        - Do NOT include any explanations, markdown formatting, or additional text.
        - If the list is too long, only include the first 50 protein names.

        ⚠️ Do not wrap the output in markdown (e.g., no ```python or ```).
        Don't assign the list to a variable.
        Only return the Python assignment line.
        '''

        user_prompt = f'''
        Question: {question},
        Data: {data}
        '''

        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": "The proteins that match the question are: "}
        ]


    def analyze(self, question: str, sql: str, df: pd.DataFrame) -> str:
        # 1. Preprocess the data
        processed_data = self._preprocess_dataframe(df)
        
        # 2. Format data for LLM
        formatted_data = {
            "schema": {str(k): str(v) for k, v in df.dtypes.items()},
            "data_sample": processed_data,
            "summary": {
                "total_rows": len(df),
                "columns": list(df.columns),
                "missing_values": df.isnull().sum().to_dict()
            }
        }
        
        # 3. Create message for LLM
        messages = self.make_message(question, sql, formatted_data)
        
        # 4. Get LLM response
        completion = self.client.chat.completions.create(
            messages=messages,
            model="unused",
            temperature=0
        )
        
        return ast.literal_eval(completion.choices[0].message.content)

    def _preprocess_dataframe(self, df: pd.DataFrame, max_rows=100):
        # Convert to records format
        df_sample = df.head(max_rows) if len(df) > max_rows else df
        return df_sample.to_dict(orient='records')
    
def get_analysis_agent(model: str = "md_anderson"):
    return AnalysisAgent(model)
    

if __name__ == "__main__":
    question = "What are the proteins that are important for breast cancer?"
    sql = "SELECT * FROM proteins WHERE cancer_type = 'breast'"
    # create synthetic data
    df = pd.DataFrame({
        "protein_id": ["P02649", "P02650", "P02651"],
        "cancer_type": ["breast", "breast", "breast"],
        "citrullination": [True, False, True]
    })
    analysis_agent = get_analysis_agent(model="md_anderson")
    result = analysis_agent.analyze(question, sql, df)
    print(result)

