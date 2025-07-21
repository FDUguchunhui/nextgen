import os
import gradio as gr
from nextgen.agents import get_data_scientist_agent, get_analysis_agent, get_statistician_agent, get_cross_reference_agent
import logging
import sys
from datetime import datetime
import tempfile

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
    def __init__(self, model: str = 'md_anderson'):
        logger.info("Initializing ChatInterface...")
        self.data_scientist_agent = get_data_scientist_agent(model=model, chroma_path='database/data_scientist_chroma')
        self.analysis_agent = get_analysis_agent(model=model)
        self.statistician_agent = get_statistician_agent(model=model)
        self.cross_reference_agent = get_cross_reference_agent(model=model)
        
        # Create temp directory for downloads
        self.temp_dir = tempfile.mkdtemp()
        logger.info("ChatInterface initialized successfully")
        
    def save_dataframe_to_temp(self, df, filename):
        """Save dataframe to temporary file and return the path"""
        if df is not None and not df.empty:
            filepath = os.path.join(self.temp_dir, filename)
            df.to_csv(filepath, index=False)
            return filepath
        return None
        
    def process_query(self, message, history=None):
        if history is None:
            history = []
        
        raw_df_file = None
        stat_result_file = None
        
        try:
            # 1. Data retrieval
            history.append({"role": "user", "content": message})
            assistant_msg = "================================================\n"
            assistant_msg += "Generating SQL query and fetching data..."
            history.append({"role": "assistant", "content": assistant_msg})
            yield history, None, None

            df, sql = self.data_scientist_agent.analyze(message)
            assistant_msg = f"SQL query generated: ```sql\n{sql}\n```"
            history.append({"role": "assistant", "content": assistant_msg})
            yield history, None, None

            # Save raw data to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            raw_df_file = self.save_dataframe_to_temp(df, f"raw_data_{timestamp}.csv")

            # 2. Show data preview with download option
            assistant_msg = "================================================\n"
            assistant_msg = f"Retrieved data with {len(df)} rows and {len(df.columns)} columns.\n\n" + \
                            f"Raw Data (preview):\n{df.head(10).to_markdown(index=False)}\n\n" + \
                            "📁 **Raw data file is ready for download!**"
            history.append({"role": "assistant", "content": assistant_msg})
            yield history, raw_df_file, None

            # 3. Statistics
            assistant_msg = "================================================\n"
            assistant_msg += "Running t-test analysis..."
            history.append({"role": "assistant", "content": assistant_msg})
            yield history, raw_df_file, None

            stat_result = self.statistician_agent.analyze(
                'Perform a two-sample t-test for each unique protein comparing expression levels between the cancer types',
                df
            )

            # Save statistical results to file
            stat_result_file = self.save_dataframe_to_temp(stat_result, f"statistical_results_{timestamp}.csv")

            # 4. Show statistical results with download option
            assistant_msg = "================================================\n"
            assistant_msg += f"Retrieved statistical data with {len(stat_result)} rows and {len(stat_result.columns)} columns.\n\n" + \
                            f"Statistical analysis results (preview):\n{stat_result.head(10).to_markdown(index=False)}\n\n" + \
                            "📊 **Statistical results file is ready for download!**"
            history.append({"role": "assistant", "content": assistant_msg})
            yield history, raw_df_file, stat_result_file

            # 5. Analysis
            assistant_msg = "================================================\n"
            assistant_msg += "Analyzing results..."
            history.append({"role": "assistant", "content": assistant_msg})
            yield history, raw_df_file, stat_result_file

            analysis_result = self.analysis_agent.analyze(message, sql, stat_result)
            assistant_msg = "Analysis complete."
            history.append({"role": "assistant", "content": assistant_msg})
            yield history, raw_df_file, stat_result_file

            # 6. Cross-reference
            assistant_msg = "================================================\n"
            assistant_msg = "Cross-referencing results..."
            history.append({"role": "assistant", "content": assistant_msg})
            yield history, raw_df_file, stat_result_file

            final_result = self.cross_reference_agent.analyze(
                question=analysis_result,
                proteins=analysis_result
            )
            assistant_msg = "Cross-reference complete."
            history.append({"role": "assistant", "content": assistant_msg})
            yield history, raw_df_file, stat_result_file

            # Final result
            history.append({"role": "assistant", "content": final_result})
            yield history, raw_df_file, stat_result_file

        except Exception as e:
            history.append({"role": "assistant", "content": f"**Error:** {str(e)}"})
            yield history, raw_df_file, stat_result_file

def main():
    logger.info("Starting Gradio chat interface...")
    chat_interface = ChatInterface()
    
    # Create custom interface with Blocks
    with gr.Blocks(title="NextAGent Chat", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# NextGen Protein Analysis Chat")
        gr.Markdown("Ask questions about protein expression data and cancer types. The system will analyze the data and provide statistical insights.")
        
        with gr.Row():
            with gr.Column(scale=4):
                chatbot = gr.Chatbot(
                    height=600,
                    show_label=False,
                    avatar_images=(
                        "../img/user.jpeg", 
                        "../img/assistant.jpg"
                    )
                )
                
                msg = gr.Textbox(
                    placeholder="Ask a question about protein analysis...",
                    show_label=False,
                    container=False
                )
                
                # Example buttons
                with gr.Row():
                    example1 = gr.Button("Example 1: Extract protein data for breast & gastric cancer", size="sm")
                    example2 = gr.Button("Example 2: Most differentially expressed proteins", size="sm")
                    example3 = gr.Button("Example 3: Protein expression in breast cancer", size="sm")
                
            with gr.Column(scale=1):
                gr.Markdown("### 📁 Download Files")
                gr.Markdown("Download intermediate analysis files when available:")
                
                raw_data_download = gr.DownloadButton(
                    label="📊 Download Raw Data (CSV)",
                    value=None,
                    visible=False
                )
                
                stat_results_download = gr.DownloadButton(
                    label="📈 Download Statistical Results (CSV)", 
                    value=None,
                    visible=False
                )
                
                gr.Markdown("---")
                gr.Markdown("**Files will appear here as they become available during analysis.**")

        def user_message(message, history):
            return "", history + [[message, None]]

        def bot_response(history):
            message = history[-1][0]
            
            # Process the query and get streaming response
            for response_history, raw_file, stat_file in chat_interface.process_query(message, []):
                # Convert internal format to chatbot format
                chatbot_history = []
                
                if len(response_history) > 0:
                    # First message is the user message
                    user_msg = response_history[0]["content"]
                    
                    # Collect all assistant messages and combine them
                    assistant_messages = []
                    for i in range(1, len(response_history)):
                        if response_history[i]["role"] == "assistant":
                            assistant_messages.append(response_history[i]["content"])
                    
                    # Combine all assistant messages with double line breaks
                    combined_bot_msg = "\n\n".join(assistant_messages) if assistant_messages else ""
                    
                    if combined_bot_msg:
                        chatbot_history.append([user_msg, combined_bot_msg])
                
                # Update download buttons visibility and files
                raw_visible = raw_file is not None
                stat_visible = stat_file is not None
                
                yield (chatbot_history, 
                       gr.update(value=raw_file, visible=raw_visible),
                       gr.update(value=stat_file, visible=stat_visible))

        # Event handlers
        msg.submit(user_message, [msg, chatbot], [msg, chatbot]).then(
            bot_response, [chatbot], [chatbot, raw_data_download, stat_results_download]
        )
        
        # Example button handlers
        def set_example(example_text):
            return example_text
            
        example1.click(
            set_example, 
            inputs=gr.State("Extract protein expression data and cancer type for protein. Only extract proteins from breast cancer and gastric cancer."), 
            outputs=msg
        )
        example2.click(
            set_example,
            inputs=gr.State("What are the most differentially expressed proteins between breast cancer and gastric cancer?"),
            outputs=msg
        )
        example3.click(
            set_example,
            inputs=gr.State("Show me the protein expression levels in breast cancer samples."),
            outputs=msg
        )
    
    logger.info("Launching Gradio interface...")
    demo.queue()  # Enable queuing for streaming updates
    demo.launch(share=True, server_name="0.0.0.0")

if __name__ == "__main__":
    main() 