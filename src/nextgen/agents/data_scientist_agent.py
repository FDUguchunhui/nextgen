# research question to query
# for example
# What proteins are important for breast cancer
# is: extract protein expression data and sample type for protein and rename other type to other

import os
from vanna.chromadb import ChromaDB_VectorStore
from nextgen.agents.agents import Agent
from nextgen.vanna.client import MDAndersonLLM_Chat
from vanna.openai import OpenAI_Chat


initial_prompt = f"""
            You are a skilled data scientist specializing in database querying and data analysis. 
            Your task is to generate a **step-by-step query plan** and a SQL query that can generate data needed to answer a research question using the given database schema and metadata.

            The query plan should:
            - Be written as an ordered list of steps.
            - Be specific enough to guide SQL query writing.
            - Use terms consistent with the table and column names provided.
            - Include filtering, grouping, joining, or renaming logic where necessary.
            - Help structure complex logic into understandable and modular operations.
            - You should only generate query plan to prepare the data, you shouldn't perform any data analysis in the query plan (i.e. you shouldn't use any aggregate functions like count, sum, avg, etc.).
            - keep the data in long format and only keep the columns that are needed to answer the question.

            If the question contains only one cancer type, you should compare it will all other cancer types.

            Example 1:
            **Question**: "What proteins are important for distinguishing between breast and gastric cancer?"
            **Query Plan**:
            1. Identify the table that contains protein expression and sample metadata.
            2. Filter the data to include only samples from breast and gastric cancer.
            3. Relabel other cancer types as 'other' when you are asked to compared one cancer type between some other cancer types (e.g. breast and all other cancer types).

            Now, given the following question and database description, write a detailed query plan and SQL query. The SQL query should be executable and free of syntax errors and enclosed in "```sql" and "```" tags. You must provide the SQL query in the response.
"""




def get_vanna_instance(model: str = 'md_anderson', chroma_path: str = 'database/data_scientist_chroma', sql_path: str = 'database/nextgen.db'):
    
    if model == 'md_anderson':
        api_key = os.getenv('APIM_SUBSCRIPTION_KEY')
        if not api_key:
            raise RuntimeError("Missing required environment variable: APIM_SUBSCRIPTION_KEY")

        class MyVanna(ChromaDB_VectorStore, MDAndersonLLM_Chat):
            def __init__(self, config=None):
                MDAndersonLLM_Chat.__init__(self, config=config)
                ChromaDB_VectorStore.__init__(self, config=config)
        
        config = {
            'APIM_SUBSCRIPTION_KEY': api_key,
            'path': chroma_path,
            'initial_prompt': initial_prompt
            }

    elif model == 'openai':
        class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
            def __init__(self, config=None):
                OpenAI_Chat.__init__(self, config=config)
                ChromaDB_VectorStore.__init__(self, config=config)

        config={'api_key': os.getenv('OPENAI_API_KEY'),
                'model': 'gpt-4.1',
                'path': chroma_path,
                'initial_prompt': initial_prompt,
                'temperature': 0.0}
    vn = MyVanna(config=config)
    vn.connect_to_sqlite(sql_path)
    return vn

class DataScientistAgent(Agent):

    def __init__(self, vanna_instance=None):
        super().__init__()
        
        self.vn = vanna_instance

    def analyze(self, question: str) -> str:
        sql, df, _ = self.vn.ask(question=question, auto_train=False, allow_llm_to_see_data=True)
        return df, sql
    
def get_data_scientist_agent(model: str = 'md_anderson', chroma_path: str = 'database/data_scientist_chroma'):
    return DataScientistAgent(vanna_instance=get_vanna_instance(model=model, chroma_path=chroma_path))


if __name__ == "__main__":
    agent = get_data_scientist_agent('openai')
    # Extract protein expression data and cancer type for protein. Only extract proteins from breast cancer and gastric cancer.
    # query_plan = agent.generate_query_plan("What proteins are important for distinguishing between breast and all other cancer types?")
    # question = "What proteins could be good biomarkers for breast cancer?"
    question = "How many proteins with citrullination? Only extract proteins from breast cancer."
    df = agent.analyze(question)
    # df = agent.analyze("Extract protein expression data and cancer type for protein. Only extract proteins from breast cancer and gastric cancer?")
    print(df)