from typing import Optional, Union, List
import pandas as pd
import os
from pandasai import Agent
import pandasai as pai
# from pandasai_openai import OpenAI
from pandasai.ee.vectorstores import ChromaDB
from pandasai import SmartDataframe
from nextgen.pandas.client import MDAndersonLLM
from nextgen.analysis.t_test import perform_t_test

class StatisticianAgent:
    """
    A statistical analysis agent that can answer questions about pandas dataframes
    using natural language queries.
    """
    
    def __init__(self, vector_store_path: str = "database/statistician_chroma", additional_dependencies: List[str] = None):
        """
        Initialize the statistician agent.
        
        Args:
            api_base_url: Base URL for the OpenAI API
            additional_dependencies: Additional Python packages to whitelist for analysis
        """
        self.vector_store_path = vector_store_path
        self.client = MDAndersonLLM()
        
        # Default dependencies for statistical analysis
        self.dependencies = ["scipy", "statistics", "numpy", "pandas", "scikit-learn", "warnings"]
        if additional_dependencies:
            self.dependencies.extend(additional_dependencies)
            

    def analyze(
        self,
        question: str,
        df: pd.DataFrame
    ) -> Union[str, pd.DataFrame]:
        """
        Analyze a pandas dataframe based on a natural language question.
        
        Args:
            df: The pandas dataframe to analyze
            question: The question to answer about the data
            enable_cache: Whether to enable caching of results
            
        Returns:
            The answer to the question, either as a string or a pandas dataframe
        
        Raises:
            ValueError: If the dataframe is empty or the question is empty
            Exception: If there's an error during analysis
        """
        if df.empty:
            raise ValueError("The provided dataframe is empty")
        if not question.strip():
            raise ValueError("Please provide a valid question")
            
        try:
            # Print data info for debugging
            print("\nDataframe Info:")
            print(df.info())
            print("\nDataframe Head:")
            print(df.head())
            print("\nColumn Names:", df.columns.tolist())
            print("\nData Types:\n", df.dtypes)
            
            config = {
                "llm": self.client,
                "custom_whitelisted_dependencies": self.dependencies,
                "enable_cache": True,
                'enable_charts': False,
                "save_charts": False,
                "verbose": True  # Enable verbose mode for debugging
            }
            
            # create chroma vectorstore
            vector_store = ChromaDB(persist_path=self.vector_store_path)
            agent = Agent(df, memory_size=100, config=config, vectorstore=vector_store)

            agent.train(queries=["The data is protein expression data with each row is a protein in a sample of cancer type. Perform t-test for each protein between the two group"],
                         codes=[perform_t_test.__code__])
            
            # Get the response
            # sdf = SmartDataframe(df, config=config)
            # response = sdf.chat(question)
            system_prompt = '''
            You are a data analyst working with protein expression data in a long-format DataFrame. Each row represents the expression level of a specific protein from a sample associated with a particular cancer type.

            When performing statistical analysis between two cancer types, follow these guidelines:
            1. Use vectorized operations. Avoid explicit for-loops. Prefer efficient methods using pandas or NumPy, such as groupby, pivot, or broadcasting. You should sacrifice for readability to achieve better performance.
            2. Always include necessary imports at the top of the code. For example, use `import numpy as np` if you are using NumPy functions like log2 or log1p.
            3. Before comparing expression levels, check that each protein is present in at least two cancer types. If not, skip the protein.
            4. Perform a statistical test (e.g., two-sample t-test) to compare expression levels between the two cancer types.
            5. Calculate the ROC AUC for each protein using using roc_auc_score from sklearn.metrics
            6. Output the number of samples in each group.
            7. Compute the log2-fold change: `log2(mean_group1 / mean_group2)` - **To avoid divide-by-zero**, if either group's mean is 0, set `log2_fold_change = 0`.
            8. Return a summary DataFrame with the following columns: 'protein_group', 'mean_intensity_{group1}', 'mean_intensity_{group2}', 'log2_fold_change', 'number_of_samples_{group1}', 'number_of_samples_{group2}', 'p_val', 'auc'.
            9. Sort the results by 'auc' in descending order and 'p_val' in ascending order.
            10. Suppress an warning message.
            '''

            response = agent.chat(system_prompt + question)
            return response
            
        except Exception as e:
            print(f"\nError details: {str(e)}")
            raise Exception(f"Error analyzing data: {str(e)}")
    

def get_statistician_agent(vector_store_path: str = "database/statistician_chroma"):
    return StatisticianAgent(vector_store_path)

if __name__ == "__main__":
    # Read the data with explicit data types
    df = pd.read_csv("data/test_statistician.csv")
    
    question = (
    '''
    Perform a two-sample t-test for each unique protein comparing expression levels between the two cancer types.
    '''
)
    # question = "How many proteins are there in the data?"
    statistician = get_statistician_agent()
    response = statistician.analyze(question, df)
    print("\nResponse:", response)