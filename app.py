import streamlit as st
import pandas as pd
from chatbot.financial_chatbot import FinancialChatbot
from loader.financial_data_loader import FinancialDataLoader
from utils import utils
import uvicorn
import multiprocessing
import os
import sys

class StreamlitApp:
    def __init__(self):
        # Initialize Streamlit settings
        st.set_page_config(page_title=f'Langchain Demo [model:{utils.model_name}]', layout="wide")
        self.context_aware_key = "context_aware"

        # Initialize session state
        if self.context_aware_key not in st.session_state:
            st.session_state[self.context_aware_key] = True

        # Initialize FinancialChatbot
        self.chatbot = FinancialChatbot()
        self.financial_data_loader = FinancialDataLoader()

    def flip_context_aware(self):
        st.session_state[self.context_aware_key] = not st.session_state[self.context_aware_key]

    def display_sidebar(self):
        """Displays the sidebar with context-aware checkbox and file uploader."""
        with st.sidebar:  
            st.checkbox(
                "Context Aware",
                value=st.session_state[self.context_aware_key],
                key="check",
                on_change=self.flip_context_aware
            )
            uploaded_file = st.file_uploader("Add more context", type="pdf")
            if uploaded_file:
                self.financial_data_loader.load_and_split_pdf(uploaded_file)
            
            ticker = st.text_input("Add ticker context")
            if ticker:
                urls = self.financial_data_loader.load_vector_db(tickers=[ticker])
                st.write(f"Loaded {len(urls)} PDFs for {ticker}")
    
    def display_main_content(self):
        """Displays the main content area with question input and results."""
        
        retrieval_chain_ = self.chatbot.retrieval_chain(st.session_state[self.context_aware_key])

        input_text = st.text_input("Question:")

        if input_text:
            result = retrieval_chain_.invoke({"question": input_text})

            if isinstance(result, dict):
                st.table(pd.DataFrame(result))
            else:
                #st.write(f"Generating plain text with {self.chatbot.create_prompt_template(st.session_state[self.context_aware_key])}")
                st.write(result)

    def run(self):
        """Runs the Streamlit application."""
        self.display_sidebar()
        self.display_main_content()

def run_fastapi():
    """Run the FastAPI server"""
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)

def run_streamlit():
    """Run the Streamlit server"""
    os.system(f"{sys.executable} -m streamlit run streamlit_app.py --server.port 8501")

if __name__ == "__main__":
    # Start both servers in separate processes
    fastapi_process = multiprocessing.Process(target=run_fastapi)
    streamlit_process = multiprocessing.Process(target=run_streamlit)

    # Start the processes
    fastapi_process.start()
    streamlit_process.start()

    try:
        # Wait for both processes to complete
        fastapi_process.join()
        streamlit_process.join()
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        fastapi_process.terminate()
        streamlit_process.terminate()
        fastapi_process.join()
        streamlit_process.join()
        print("Servers shut down successfully")
