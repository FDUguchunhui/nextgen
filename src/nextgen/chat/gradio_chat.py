import os
import gradio as gr
from vanna.chromadb import ChromaDB_VectorStore
from nextgen.vanna.client import MyVanna
from nextgen.agents.analysis_agent import AnalysisAgent
from nextgen.agents.statistician_agent import StatisticianAgent
from nextgen.agents.cross_reference_agent import CrossReferenceAgent
import pandas as pd
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
    def __init__(self):
        logger.info("Initializing ChatInterface...")
        config = {
            'APIM_SUBSCRIPTION_KEY': os.getenv('APIM_SUBSCRIPTION_KEY'),
            'path': 'database/chroma'
        }
        self.vn = MyVanna(config=config)
        self.vn.connect_to_sqlite('database/nextgen.db')
        self.analysis_agent = AnalysisAgent()
        self.statistician_agent = StatisticianAgent()
        self.cross_reference_agent = CrossReferenceAgent('MDA')
        logger.info("ChatInterface initialized successfully")
        
    def process_query(self, message, history):
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            progress_msg = ""
            
            def log_progress(msg):
                nonlocal progress_msg
                logger.info(msg)
                progress_msg += f"[{timestamp}] {msg}\n"
            
            log_progress(f"Processing query: {message}")
            
            # Get SQL and data from Vanna
            log_progress("Generating SQL query and fetching data...")
            sql, df, _ = self.vn.ask(question=message, auto_train=False)
            log_progress(f"SQL query generated: {sql}")
            
            # Save intermediate results
            temp_csv = 'data/temp_analysis.csv'
            df.to_csv(temp_csv, index=False)
            log_progress(f"Retrieved data with {len(df)} rows and {len(df.columns)} columns")
            
            # Run statistical analysis if the data contains protein expression data
            log_progress("Running t-test analysis...")
            stat_result = self.statistician_agent.analyze(
                'Perform a two-sample t-test for each unique protein comparing expression levels between the cancer types',
                df
            )
            log_progress("Statistical analysis complete")
            
            log_progress("Analyzing results...")
            analysis_result = self.analysis_agent.analyze(message, sql, stat_result)
            log_progress("Analysis complete")
            
            log_progress("Cross-referencing results...")
            final_result = self.cross_reference_agent.analyze(
                question=analysis_result,
                proteins=analysis_result
            )
            log_progress("Cross-reference complete")
            
            # Only yield the final result without any additional text
            yield final_result

            
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            yield str(e)

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