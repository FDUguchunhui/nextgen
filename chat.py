from nextgen.agents.analysis_agent import AnalysisAgent
from nextgen.agents.statistician_agent import StatisticianAgent
from nextgen.agents.cross_reference_agent import CrossReferenceAgent
from nextgen.agents.data_scientist_agent import get_data_scientist_agent

question = "What proteins are important for distinguishing between breast and all other cancer types?"
data_scientist_agent = get_data_scientist_agent()
raw_data, sql = data_scientist_agent.analyze(question=question)

statistician_agent = StatisticianAgent()
statistician_result = statistician_agent.analyze('Perform a two-sample t-test for each unique protein comparing expression levels between the two cancer types. Filter proteins with p-value less than 0.05.', raw_data)

print(statistician_result.head(10))

analysis_agent = AnalysisAgent()
analysis_result = analysis_agent.analyze(question, sql, statistician_result)

# cross reference the result
cross_reference_agent = CrossReferenceAgent('MDA')
cross_reference_result = cross_reference_agent.analyze(question=analysis_result, proteins=analysis_result)
print(cross_reference_result)