import os
import gradio as gr
from nextgen.agents.data_scientist_agent import get_data_scientist_agent
from nextgen.agents.analysis_agent import AnalysisAgent
from nextgen.agents.statistician_agent import StatisticianAgent
from nextgen.agents.cross_reference_agent import CrossReferenceAgent
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('chat_logs.txt')
    ]
)
logger = logging.getLogger(__name__)

class ChatInterface:
    def __init__(self, model: str = 'openai'):
        logger.info("Initializing ChatInterface...")
        self.data_scientist_agent = get_data_scientist_agent(model=model, chroma_path='database/data_scientist_chroma')
        self.analysis_agent = AnalysisAgent()
        self.statistician_agent = StatisticianAgent()
        self.cross_reference_agent = CrossReferenceAgent(model=model)
        logger.info("ChatInterface initialized successfully")
        
    def process_query(self, message, history=None):
        if history is None:
            history = []
        try:
            # 1. Data retrieval
            history.append({"role": "user", "content": message})
            assistant_msg = "Generating SQL query and fetching data..."
            history.append({"role": "assistant", "content": assistant_msg})
            yield history

            df, sql = self.data_scientist_agent.analyze(message)
            assistant_msg = f"SQL query generated: ```sql\n{sql}\n```"
            history.append({"role": "assistant", "content": assistant_msg})
            yield history

            # 2. Show data preview
            assistant_msg = f"Retrieved data with {len(df)} rows and {len(df.columns)} columns.\n\n" + \
                            f"Raw Data (preview):\n{df.head(10).to_markdown(index=False)}"
            history.append({"role": "assistant", "content": assistant_msg})
            yield history

            # 3. Statistics
            assistant_msg = "Running t-test analysis..."
            history.append({"role": "assistant", "content": assistant_msg})
            yield history

            stat_result = self.statistician_agent.analyze(
                'Perform a two-sample t-test for each unique protein comparing expression levels between the cancer types',
                df
            )

            # 3. Show data preview
            assistant_msg = f"Retrieved data with {len(df)} rows and {len(df.columns)} columns.\n\n" + \
                            f"Raw Data (preview):\n{df.head(10).to_markdown(index=False)}"
            history.append({"role": "assistant", "content": assistant_msg})
            yield history

            # 4. Statistics
            assistant_msg = "Statistical analysis complete."
            history.append({"role": "assistant", "content": assistant_msg})
            yield history

            # 4. Analysis
            assistant_msg = "Analyzing results..."
            history.append({"role": "assistant", "content": assistant_msg})
            yield history

            analysis_result = self.analysis_agent.analyze(message, sql, stat_result)
            assistant_msg = "Analysis complete."
            history.append({"role": "assistant", "content": assistant_msg})
            yield history

            # 5. Cross-reference
            assistant_msg = "Cross-referencing results..."
            history.append({"role": "assistant", "content": assistant_msg})
            yield history

            final_result = self.cross_reference_agent.analyze(
                question=analysis_result,
                proteins=analysis_result
            )
            assistant_msg = "Cross-reference complete."
            history.append({"role": "assistant", "content": assistant_msg})
            yield history

            # Only yield the final result without any additional text
            history.append({"role": "assistant", "content": final_result})
            yield history

        except Exception as e:
            history.append({"role": "assistant", "content": f"**Error:** {str(e)}"})
            yield history

def main():
    logger.info("Starting Gradio chat interface...")
    chat_interface = ChatInterface()
    
    demo = gr.ChatInterface(
        chat_interface.process_query,
        title="NextGen Protein Analysis Chat",
        description="Ask questions about protein expression data and cancer types. The system will analyze the data and provide statistical insights.",
        examples=[
            "Extract protein expression data and cancer type for protein. Only extract proteins from breast cancer and gastric cancer.",
            "What are the most differentially expressed proteins between breast cancer and gastric cancer?",
            "Show me the protein expression levels in breast cancer samples."
        ],
        theme=gr.themes.Soft()
    )
    
    logger.info("Launching Gradio interface...")
    demo.queue()  # Enable queuing for streaming updates
    demo.launch(share=True, server_name="0.0.0.0")

if __name__ == "__main__":
    main() 