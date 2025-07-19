import os
from vanna.chromadb import ChromaDB_VectorStore
from nextgen.vanna.llama import MyVanna
from nextgen.agents.analysis_agent import AnalysisAgent
from nextgen.agents.statistician_agent import StatisticianAgent
from nextgen.agents.cross_reference_agent import CrossReferenceAgent

config={
    'APIM_SUBSCRIPTION_KEY': os.getenv('APIM_SUBSCRIPTION_KEY'),
    'path': 'database/chroma'
    }

vn = MyVanna(config=config)
vn.connect_to_sqlite('database/nextgen.db')

question = "Extract protein expression data and cancer type for protein. Only extract proteins from breast cancer and gastric cancer."
sql, df, _ = vn.ask(question=question, auto_train=False)
# save the dataframe to a csv file
df.to_csv('data/test_statistician.csv', index=False)

statistician_agent = StatisticianAgent()
statistician_result = statistician_agent.analyze('Perform a two-sample t-test for each unique protein comparing expression levels between the two cancer types', df)

print(statistician_result.head(10))

analysis_agent = AnalysisAgent()
analysis_result = analysis_agent.analyze(question, sql, statistician_result)

# cross reference the result
cross_reference_agent = CrossReferenceAgent('MDA')
cross_reference_result = cross_reference_agent.analyze(question=analysis_result, proteins=analysis_result)
print(cross_reference_result)