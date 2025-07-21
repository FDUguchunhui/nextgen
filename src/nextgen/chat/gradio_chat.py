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

# Custom CSS for enhanced styling
custom_css = """
/* Main container styling */
.gradio-container {
    max-width: 1400px !important;
    margin: 0 auto !important;
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif !important;
}

/* Header styling */
.header-container {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 2rem;
    border-radius: 15px;
    margin-bottom: 2rem;
    color: white;
    text-align: center;
    box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
}

.header-title {
    font-size: 2.5rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

.header-subtitle {
    font-size: 1.2rem;
    opacity: 0.9;
    font-weight: 300;
}

/* Chatbot container styling */
.chatbot-container {
    background: white;
    border-radius: 20px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.1);
    padding: 1.5rem;
    margin-bottom: 1rem;
    border: 1px solid #e1e5e9;
}

/* Input area styling */
.input-container {
    background: #f8fafc;
    border-radius: 15px;
    padding: 1rem;
    border: 2px solid #e2e8f0;
    transition: all 0.3s ease;
    margin-right: 0.5rem;
}

.input-container:focus-within {
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

/* Input row styling */
.input-row {
    display: flex;
    align-items: flex-end;
    gap: 0.5rem;
}

/* Send button styling */
.send-btn {
    background: linear-gradient(45deg, #4ade80 0%, #22c55e 100%);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 1rem 1.5rem;
    margin-left: 0.5rem;
    font-weight: 600;
    font-size: 1rem;
    height: 100%;
    min-height: 60px;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(74, 222, 128, 0.3);
}

.send-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(74, 222, 128, 0.4);
    background: linear-gradient(45deg, #22c55e 0%, #16a34a 100%);
}

.send-btn:active {
    transform: translateY(0px);
    box-shadow: 0 2px 8px rgba(74, 222, 128, 0.4);
}

/* Example buttons styling */
.example-btn {
    background: linear-gradient(45deg, #f093fb 0%, #f5576c 100%);
    color: white;
    border: none;
    border-radius: 25px;
    padding: 0.75rem 1.5rem;
    margin: 0.25rem;
    font-weight: 500;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(240, 147, 251, 0.3);
}

.example-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(240, 147, 251, 0.4);
}

/* Download section styling */
.download-section {
    background: linear-gradient(145deg, #ffffff, #f0f4f8);
    border-radius: 20px;
    padding: 1.5rem;
    box-shadow: 0 8px 25px rgba(0,0,0,0.08);
    border: 1px solid #e2e8f0;
}

.download-title {
    font-size: 1.3rem;
    font-weight: 600;
    color: #2d3748;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.download-btn {
    background: linear-gradient(45deg, #4facfe 0%, #00f2fe 100%);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 0.75rem 1.25rem;
    margin: 0.5rem 0;
    font-weight: 500;
    width: 100%;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(79, 172, 254, 0.3);
}

.download-btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(79, 172, 254, 0.4);
}

.download-btn:disabled {
    background: #e2e8f0;
    color: #a0aec0;
    transform: none;
    box-shadow: none;
}

/* Info card styling */
.info-card {
    background: linear-gradient(145deg, #fff5f5, #fed7d7);
    border-left: 4px solid #f56565;
    padding: 1rem;
    border-radius: 8px;
    margin: 1rem 0;
    font-size: 0.9rem;
    color: #2d3748;
}

/* Status indicators */
.status-indicator {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 0.5rem;
}

.status-processing {
    background: #fbbf24;
    animation: pulse 2s infinite;
}

.status-complete {
    background: #10b981;
}

.status-error {
    background: #ef4444;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

/* Responsive design */
@media (max-width: 768px) {
    .gradio-container {
        padding: 1rem;
    }
    
    .header-title {
        font-size: 2rem;
    }
    
    .header-subtitle {
        font-size: 1rem;
    }
    
    .example-btn {
        padding: 0.5rem 1rem;
        font-size: 0.9rem;
    }
}

/* Message styling */
.user-message {
    background: linear-gradient(45deg, #667eea, #764ba2);
    color: white;
    border-radius: 18px 18px 4px 18px;
    padding: 1rem;
    margin: 0.5rem 0;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.bot-message {
    background: #f7fafc;
    border: 1px solid #e2e8f0;
    border-radius: 18px 18px 18px 4px;
    padding: 1rem;
    margin: 0.5rem 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

/* Loading animation */
.loading-dots {
    display: inline-block;
}

.loading-dots::after {
    content: '';
    animation: dots 1.5s infinite;
}

@keyframes dots {
    0%, 20% { content: ''; }
    40% { content: '.'; }
    60% { content: '..'; }
    80%, 100% { content: '...'; }
}
"""

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
            assistant_msg = "🔍 **Generating SQL query and fetching data...**\n"
            assistant_msg += "<div class='status-indicator status-processing'></div> Analyzing your request and building database query"
            history.append({"role": "assistant", "content": assistant_msg})
            yield history, None, None

            df, sql = self.data_scientist_agent.analyze(message)
            assistant_msg = f"✅ **SQL Query Generated Successfully**\n\n"
            assistant_msg += f"```sql\n{sql}\n```\n\n"
            assistant_msg += f"<div class='status-indicator status-complete'></div> Query executed successfully"
            history.append({"role": "assistant", "content": assistant_msg})
            yield history, None, None

            # Save raw data to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            raw_df_file = self.save_dataframe_to_temp(df, f"raw_data_{timestamp}.csv")

            # 2. Show data preview with download option
            assistant_msg = f"📊 **Data Retrieved Successfully**\n\n"
            assistant_msg += f"• **Rows:** {len(df):,}\n"
            assistant_msg += f"• **Columns:** {len(df.columns)}\n"
            assistant_msg += f"• **Data Types:** {', '.join(df.dtypes.astype(str).unique())}\n\n"
            assistant_msg += f"**📋 Data Preview (First 10 rows):**\n\n"
            assistant_msg += f"{df.head(10).to_markdown(index=False)}\n\n"
            assistant_msg += "🎉 **Raw data file is ready for download!**"
            history.append({"role": "assistant", "content": assistant_msg})
            yield history, raw_df_file, None

            # 3. Statistics
            assistant_msg = "📈 **Running Statistical Analysis...**\n"
            assistant_msg += "<div class='status-indicator status-processing'></div> Performing two-sample t-tests for protein comparisons"
            history.append({"role": "assistant", "content": assistant_msg})
            yield history, raw_df_file, None

            stat_result = self.statistician_agent.analyze(
                'Perform a two-sample t-test for each unique protein comparing expression levels between the cancer types',
                df
            )

            # Save statistical results to file
            stat_result_file = self.save_dataframe_to_temp(stat_result, f"statistical_results_{timestamp}.csv")

            # 4. Show statistical results with download option
            assistant_msg = f"🧮 **Statistical Analysis Complete**\n\n"
            assistant_msg += f"• **Statistical Tests:** {len(stat_result)} proteins analyzed\n"
            assistant_msg += f"• **Significant Results:** {len(stat_result[stat_result.get('p_value', 1) < 0.05]) if 'p_value' in stat_result.columns else 'N/A'}\n"
            assistant_msg += f"• **Columns:** {len(stat_result.columns)}\n\n"
            assistant_msg += f"**📊 Statistical Results Preview:**\n\n"
            assistant_msg += f"{stat_result.head(10).to_markdown(index=False)}\n\n"
            assistant_msg += "📈 **Statistical results file is ready for download!**"
            history.append({"role": "assistant", "content": assistant_msg})
            yield history, raw_df_file, stat_result_file

            # 5. Analysis
            assistant_msg = "🧠 **Analyzing Results...**\n"
            assistant_msg += "<div class='status-indicator status-processing'></div> Interpreting statistical findings and generating insights"
            history.append({"role": "assistant", "content": assistant_msg})
            yield history, raw_df_file, stat_result_file

            analysis_result = self.analysis_agent.analyze(message, sql, stat_result)
            assistant_msg = "✅ **Analysis Complete**\n"
            assistant_msg += "<div class='status-indicator status-complete'></div> Statistical interpretation finished"
            history.append({"role": "assistant", "content": assistant_msg})
            yield history, raw_df_file, stat_result_file

            # 6. Cross-reference
            assistant_msg = "🔗 **Cross-referencing Results...**\n"
            assistant_msg += "<div class='status-indicator status-processing'></div> Enriching findings with external protein databases"
            history.append({"role": "assistant", "content": assistant_msg})
            yield history, raw_df_file, stat_result_file

            final_result = self.cross_reference_agent.analyze(
                question=analysis_result,
                proteins=analysis_result
            )
            assistant_msg = "🎯 **Cross-reference Complete**\n"
            assistant_msg += "<div class='status-indicator status-complete'></div> External database enrichment finished"
            history.append({"role": "assistant", "content": assistant_msg})
            yield history, raw_df_file, stat_result_file

            # Final result
            final_msg = f"## 🎊 **Analysis Complete!**\n\n"
            final_msg += f"### 📋 **Summary**\n{final_result}\n\n"
            final_msg += "### 📁 **Files Available**\n"
            final_msg += "• Raw data CSV file with all retrieved records\n"
            final_msg += "• Statistical analysis results with p-values and effect sizes\n\n"
            final_msg += "*All files are available for download in the sidebar.* 📥"
            
            history.append({"role": "assistant", "content": final_msg})
            yield history, raw_df_file, stat_result_file

        except Exception as e:
            error_msg = f"❌ **Error Occurred**\n\n"
            error_msg += f"**Error Details:** {str(e)}\n\n"
            error_msg += "Please try rephrasing your question or contact support if the issue persists."
            history.append({"role": "assistant", "content": error_msg})
            yield history, raw_df_file, stat_result_file

def main():
    logger.info("Starting Gradio chat interface...")
    chat_interface = ChatInterface()
    
    # Create enhanced interface with Blocks
    with gr.Blocks(
        title="NextAGent AI", 
        theme=gr.themes.Soft(),
        css=custom_css
    ) as demo:
        
        # Enhanced Header
        with gr.Row():
            with gr.Column():
                gr.HTML("""
                <div class="header-container">
                    <div class="header-title">🧬 NextGen Protein Analysis Suite</div>
                    <div class="header-subtitle">
                        AI-Powered Protein Expression Analysis & Statistical Insights
                    </div>
                </div>
                """)
        
        with gr.Row():
            # Main chat area
            with gr.Column(scale=7):
                with gr.Row():
                    with gr.Column():
                        gr.HTML('<div class="chatbot-container">')
                        chatbot = gr.Chatbot(
                            height=650,
                            show_label=False,
                            avatar_images=(
                                "src/nextgen/img/user.png", 
                                None
                            ),
                            bubble_full_width=False,
                            show_copy_button=True
                        )
                        gr.HTML('</div>')
                
                # Enhanced input area
                with gr.Row():
                    with gr.Column(scale=9):
                        gr.HTML('<div class="input-container">')
                        msg = gr.Textbox(
                            placeholder="💬 Ask me anything about protein expression, cancer types, or statistical analysis...",
                            show_label=False,
                            container=False,
                            lines=2,
                            max_lines=4
                        )
                        gr.HTML('</div>')
                    with gr.Column(scale=1, min_width=100):
                        send_btn = gr.Button(
                            "🚀 Send",
                            variant="primary",
                            size="lg",
                            elem_classes=["send-btn"]
                        )
                
                # Helpful instruction
                gr.HTML("""
                <div style="text-align: center; margin: 0.5rem 0; color: #64748b; font-size: 0.9rem;">
                    💡 Type your question above and click <strong>Send</strong> or press <strong>Enter</strong> to start the analysis
                </div>
                """)
                
                # Enhanced example buttons
                gr.Markdown("### 🚀 **Quick Start Examples**")
                with gr.Row():
                    example1 = gr.Button(
                        "🔬 Extract Cancer Protein Data", 
                        elem_classes=["example-btn"],
                        variant="secondary"
                    )
                    example2 = gr.Button(
                        "📊 Find Differential Expression", 
                        elem_classes=["example-btn"],
                        variant="secondary"
                    )
                    example3 = gr.Button(
                        "🎯 Breast Cancer Analysis", 
                        elem_classes=["example-btn"],
                        variant="secondary"
                    )
                
                # Additional examples row
                with gr.Row():
                    example4 = gr.Button(
                        "🧮 Statistical Significance Test", 
                        elem_classes=["example-btn"],
                        variant="secondary"
                    )
                    example5 = gr.Button(
                        "🔍 Protein Function Analysis", 
                        elem_classes=["example-btn"],
                        variant="secondary"
                    )
            
            # Enhanced download sidebar
            with gr.Column(scale=3):
                gr.HTML("""
                <div class="download-section">
                    <div class="download-title">📁 Download Center</div>
                    <div class="info-card">
                        <strong>📋 Available Files:</strong><br>
                        Files will appear here as your analysis progresses. Each step generates downloadable results.
                    </div>
                </div>
                """)
                
                raw_data_download = gr.DownloadButton(
                    label="📊 Raw Data (CSV)",
                    value=None,
                    visible=False,
                    elem_classes=["download-btn"],
                    variant="primary"
                )
                
                stat_results_download = gr.DownloadButton(
                    label="📈 Statistical Results (CSV)", 
                    value=None,
                    visible=False,
                    elem_classes=["download-btn"],
                    variant="primary"
                )
                
                gr.HTML("""
                <div style="margin-top: 1rem; padding: 1rem; background: #f7fafc; border-radius: 8px; border: 1px solid #e2e8f0;">
                    <strong>💡 Tips:</strong><br>
                    • Be specific in your questions<br>
                    • Mention specific cancer types<br>
                    • Ask for statistical comparisons<br>
                    • Request protein function insights
                </div>
                """)
                
                gr.HTML("""
                <div style="margin-top: 1rem; padding: 1rem; background: linear-gradient(145deg, #ebf8ff, #bee3f8); border-radius: 8px; border: 1px solid #90cdf4;">
                    <strong>🎯 Analysis Pipeline:</strong><br>
                    1. 🔍 SQL Query Generation<br>
                    2. 📊 Data Retrieval<br>
                    3. 📈 Statistical Testing<br>
                    4. 🧠 Result Analysis<br>
                    5. 🔗 Cross-Reference<br>
                    6. 📋 Final Report
                </div>
                """)

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
                    
                    # Combine all assistant messages with section breaks
                    combined_bot_msg = "\n\n---\n\n".join(assistant_messages) if assistant_messages else ""
                    
                    if combined_bot_msg:
                        chatbot_history.append([user_msg, combined_bot_msg])
                
                # Update download buttons visibility and files
                raw_visible = raw_file is not None
                stat_visible = stat_file is not None
                
                yield (chatbot_history, 
                       gr.update(value=raw_file, visible=raw_visible),
                       gr.update(value=stat_file, visible=stat_visible))

        # Event handlers - both submit and send button do the same thing
        submit_event = msg.submit(user_message, [msg, chatbot], [msg, chatbot]).then(
            bot_response, [chatbot], [chatbot, raw_data_download, stat_results_download]
        )
        
        send_btn.click(user_message, [msg, chatbot], [msg, chatbot]).then(
            bot_response, [chatbot], [chatbot, raw_data_download, stat_results_download]
        )
        
        # Enhanced example button handlers
        def set_example(example_text):
            return example_text
            
        example1.click(
            set_example, 
            inputs=gr.State("Extract protein expression data and cancer type information. Focus on breast cancer and gastric cancer samples with their corresponding protein expression levels."), 
            outputs=msg
        )
        example2.click(
            set_example,
            inputs=gr.State("What are the most differentially expressed proteins between breast cancer and gastric cancer? Show me proteins with significant p-values and high fold changes."),
            outputs=msg
        )
        example3.click(
            set_example,
            inputs=gr.State("Show me detailed protein expression levels in breast cancer samples. Include statistical summaries and identify outliers."),
            outputs=msg
        )
        example4.click(
            set_example,
            inputs=gr.State("Perform comprehensive statistical analysis comparing protein expression across different cancer types. Include t-tests, effect sizes, and confidence intervals."),
            outputs=msg
        )
        example5.click(
            set_example,
            inputs=gr.State("Analyze the biological functions and pathways of significantly expressed proteins. Cross-reference with protein databases for functional insights."),
            outputs=msg
        )
    
    logger.info("Launching enhanced Gradio interface...")
    demo.queue(max_size=10)  # Enable queuing for streaming updates
    demo.launch(
        share=True, 
        server_name="0.0.0.0",
        show_api=False,
        show_error=True,
        favicon_path="src/nextgen/img/user.png" if os.path.exists("src/nextgen/img/user.png") else None
    )

if __name__ == "__main__":
    main() 