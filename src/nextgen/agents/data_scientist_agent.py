# research question to query
# for example
# What proteins are important for breast cancer
# is: extract protein expression data and sample type for protein and rename other type to other

import os
from vanna.chromadb import ChromaDB_VectorStore
from nextgen.agents.agents import Agent
from nextgen.vanna.client import MDAndersonLLM_Chat


initial_prompt = f"""
            You are a skilled data scientist specializing in database querying and data analysis. 
            Your task is to generate a **step-by-step query plan** that can generate data needed to answer a research question using the given database schema and metadata.

            The query plan should:
            - Be written as an ordered list of steps.
            - Be specific enough to guide SQL query writing.
            - Use terms consistent with the table and column names provided.
            - Include filtering, grouping, joining, or renaming logic where necessary.
            - Help structure complex logic into understandable and modular operations.
            - You should only generate query plan to prepare the data, you shouldn't perform any data analysis in the query plan (i.e. you shouldn't use any aggregate functions like count, sum, avg, etc.).
            - keep the data in long format and only keep the columns that are needed to answer the question.

            Example:
            **Question**: "What proteins are important for distinguishing between breast and gastric cancer?"
            **Query Plan**:
            1. Identify the table that contains protein expression and sample metadata.
            2. Filter the data to include only samples from breast and gastric cancer.
            3. Relabel other cancer types as 'other' when you are asked to compared one cancer type between some other cancer types (e.g. breast and all other cancer types).

            Now, given the following question and database description, write a detailed query plan and SQL query:
"""


class MyVanna(ChromaDB_VectorStore, MDAndersonLLM_Chat):
    def __init__(self, config=None):
        MDAndersonLLM_Chat.__init__(self, config=config)
        ChromaDB_VectorStore.__init__(self, config=config)

    def get_query_plan_prompt(
        self,
        initial_prompt : str,
        question: str,
        ddl_list: list,
        doc_list: list,
        **kwargs,
    ):
        """

        This method is used to generate a query plan for the LLM to generate SQL.

        Args:
            question (str): The question to generate SQL for.
            ddl_list (list): A list of DDL statements.
            doc_list (list): A list of documentation.

        Returns:
            any: The prompt for the LLM to generate SQL.
        """

        if initial_prompt is None:
            initial_prompt = f"""
            You are a skilled data scientist specializing in database querying and data analysis. 
            Your task is to generate a **step-by-step query plan** that can generate data needed to answer a research question using the given database schema and metadata. You don't need to generate the SQL query, you only need to generate the query plan.

            The query plan should:
            - Be written as an ordered list of steps.
            - Be specific enough to guide SQL query writing.
            - Use terms consistent with the table and column names provided.
            - Include filtering, grouping, joining, or renaming logic where necessary.
            - Help structure complex logic into understandable and modular operations.
            - You should only generate query plan to prepare the data, you shouldn't perform any data analysis in the query plan (i.e. you shouldn't use any aggregate functions like count, sum, avg, etc.).
            - keep the data in long format and only keep the columns that are needed to answer the question.

            Example:
            **Question**: "What proteins are important for distinguishing between breast and gastric cancer?"
            **Query Plan**:
            1. Identify the table that contains protein expression and sample metadata.
            2. Filter the data to include only samples from breast and gastric cancer.
            3. Relabel other cancer types as 'other' when you are asked to compared one cancer type between some other cancer types (e.g. breast and all other cancer types).

            Now, given the following question and database description, write a detailed query plan:
            """

        initial_prompt = self.add_ddl_to_prompt(
            initial_prompt, ddl_list, max_tokens=self.max_tokens
        )

        if self.static_documentation != "":
            doc_list.append(self.static_documentation)

        initial_prompt = self.add_documentation_to_prompt(
            initial_prompt, doc_list, max_tokens=self.max_tokens
        )

        message_log = [self.system_message(initial_prompt)]

        message_log.append(self.user_message(question))

        return message_log


    def generate_query_plan(self, question: str, allow_llm_to_see_data=False, **kwargs) -> str:
        """
        Example:
        ```python
        vn.generate_sql("What are the top 10 customers by sales?")
        ```

        Uses the LLM to generate a SQL query that answers a question. It runs the following methods:

        - [`get_similar_question_sql`][vanna.base.base.VannaBase.get_similar_question_sql]

        - [`get_related_ddl`][vanna.base.base.VannaBase.get_related_ddl]

        - [`get_related_documentation`][vanna.base.base.VannaBase.get_related_documentation]

        - [`get_sql_prompt`][vanna.base.base.VannaBase.get_sql_prompt]

        - [`submit_prompt`][vanna.base.base.VannaBase.submit_prompt]


        Args:
            question (str): The question to generate a SQL query for.
            allow_llm_to_see_data (bool): Whether to allow the LLM to see the data (for the purposes of introspecting the data to generate the final SQL).

        Returns:
            str: The SQL query that answers the question.
        """
        if self.config is not None:
            initial_prompt = self.config.get("initial_prompt", None)
        else:
            initial_prompt = None
        # question_sql_list = self.get_similar_question_sql(question, **kwargs)
        ddl_list = self.get_related_ddl(question, **kwargs)
        doc_list = self.get_related_documentation(question, **kwargs)
        prompt = self.get_query_plan_prompt(
            initial_prompt=initial_prompt,
            question=question,
            ddl_list=ddl_list,
            doc_list=doc_list,
            **kwargs,
        )
        self.log(title="Query Plan Prompt", message=prompt)
        llm_response = self.submit_prompt(prompt, **kwargs)
        self.log(title="LLM Response", message=llm_response)

        return llm_response

def get_vanna_instance():
    api_key = os.getenv('APIM_SUBSCRIPTION_KEY')
    if not api_key:
        raise RuntimeError("Missing required environment variable: APIM_SUBSCRIPTION_KEY")

    config = {
        'APIM_SUBSCRIPTION_KEY': api_key,
        'path': 'database/chroma',
        'initial_prompt': initial_prompt
    }

    vn = MyVanna(config=config)
    vn.connect_to_sqlite('database/nextgen.db')
    return vn

class DataScientistAgent(Agent):

    def __init__(self, vanna_instance=None):
        super().__init__()
        
        self.vn = vanna_instance

    def generate_query_plan(self, question: str) -> str:
        return self.vn.generate_query_plan(question)

    def analyze(self, question: str) -> str:
        query_plan = self.generate_query_plan(question)
        sql, df, _ = self.vn.ask(question=query_plan, auto_train=False, allow_llm_to_see_data=True)
        return df, sql
    
def get_data_scientist_agent():
    return DataScientistAgent(vanna_instance=get_vanna_instance())


if __name__ == "__main__":
    agent = get_data_scientist_agent()
    # Extract protein expression data and cancer type for protein. Only extract proteins from breast cancer and gastric cancer.
    # query_plan = agent.generate_query_plan("What proteins are important for distinguishing between breast and all other cancer types?")
    question = "What proteins are important for distinguishing between breast and all other cancer types?"
    df = agent.analyze(question)
    # df = agent.analyze("Extract protein expression data and cancer type for protein. Only extract proteins from breast cancer and gastric cancer?")
    print(df)