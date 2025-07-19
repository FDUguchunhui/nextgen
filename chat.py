import os
from vanna.chromadb import ChromaDB_VectorStore
from nextgen.vanna.llama import MyVanna
from nextgen.agents.analysis_agent import AnalysisAgent
from nextgen.agents.cross_reference_agent import CrossReferenceAgent

config={
    'APIM_SUBSCRIPTION_KEY': os.getenv('APIM_SUBSCRIPTION_KEY'),
    'path': 'database/chroma'
    }

vn = MyVanna(config=config)
vn.connect_to_sqlite('database/nextgen.db')

question = "Extract protein expression data and cancer type for protein and rename all other cancer type to 'other'?"
sql, df, _ = vn.ask(question=question, auto_train=False)

analysis_agent = AnalysisAgent()
analysis_result = analysis_agent.analyze(question, sql, df)

# cross reference the result
cross_reference_agent = CrossReferenceAgent('MDA')
cross_reference_result = cross_reference_agent.analyze(question=analysis_result, proteins=analysis_result)
print(cross_reference_result)