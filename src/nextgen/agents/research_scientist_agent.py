from nextgen.agents.agents import Agent
from nextgen.openai.client import MDAndersonLLM

class ResearchScientistAgent(Agent):
    def __init__(self):
        super().__init__()
        self.llm = MDAndersonLLM()

    def analyze(self, question: str) -> str:
        system_prompt = f'''
    
        '''
        response = self.llm.chat(message=question)
        return response
    

if __name__ == "__main__":
    agent = ResearchScientistAgent()
    response = agent.analyze("What proteins are important for distinguishing between breast and gastric cancer?")
    print(response)