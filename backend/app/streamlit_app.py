import streamlit as st
import pandas as pd
from chatbot.financial_chatbot import FinancialChatbot
from loader.financial_data_loader import FinancialDataLoader
from utils.utils import utils
from utils.logger import get_logger

# Get logger for this module
logger = get_logger("streamlit_app")

class StreamlitApp:
    def __init__(self):
        # Initialize Streamlit settings
        logger.info("Initializing StreamlitApp")
        st.set_page_config(page_title=f'Langchain Demo [model:{utils.model_name}]', layout="wide")
        self.context_aware_key = "context_aware"

        # Initialize session state
        if self.context_aware_key not in st.session_state:
            st.session_state[self.context_aware_key] = True
            logger.debug("Initialized context_aware session state to True")

        # Initialize FinancialChatbot
        try:
            logger.info("Initializing FinancialChatbot and FinancialDataLoader")
            self.chatbot = FinancialChatbot()
            self.financial_data_loader = FinancialDataLoader()
            logger.info("Components initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing StreamlitApp components: {str(e)}", exc_info=True)
            st.error(f"Error initializing application: {str(e)}")

    def flip_context_aware(self):
        logger.info(f"Toggling context_aware from {st.session_state[self.context_aware_key]} to {not st.session_state[self.context_aware_key]}")
        st.session_state[self.context_aware_key] = not st.session_state[self.context_aware_key]

    def display_sidebar(self):
        """Displays the sidebar with context-aware checkbox and file uploader."""
        logger.debug("Setting up sidebar components")
        with st.sidebar:  
            st.checkbox(
                "Context Aware",
                value=st.session_state[self.context_aware_key],
                key="check",
                on_change=self.flip_context_aware
            )
            uploaded_file = st.file_uploader("Add more context", type="pdf")
            if uploaded_file:
                logger.info(f"Processing uploaded PDF: {uploaded_file.name}")
                try:
                    splits = self.financial_data_loader.load_and_split_pdf(uploaded_file)
                    logger.info(f"Successfully processed PDF with {len(splits)} chunks")
                    st.success(f"Processed PDF with {len(splits)} chunks")
                except Exception as e:
                    logger.error(f"Error processing PDF: {str(e)}", exc_info=True)
                    st.error(f"Error processing PDF: {str(e)}")
            
            ticker = st.text_input("Add ticker context")
            if ticker:
                logger.info(f"Loading context for ticker: {ticker}")
                try:
                    urls = self.financial_data_loader.load_vector_db(tickers=[ticker])
                    logger.info(f"Loaded {len(urls)} PDFs for ticker: {ticker}")
                    st.write(f"Loaded {len(urls)} PDFs for {ticker}")
                except Exception as e:
                    logger.error(f"Error loading ticker context: {str(e)}", exc_info=True)
                    st.error(f"Error loading ticker context: {str(e)}")
    
    def display_main_content(self):
        """Displays the main content area with question input and results."""
        logger.debug(f"Setting up main content with context_aware: {st.session_state[self.context_aware_key]}")
        retrieval_chain_ = self.chatbot.retrieval_chain(st.session_state[self.context_aware_key])
        input_text = st.text_input("Question:")

        if input_text:
            logger.info(f"Processing question: '{input_text[:50]}...'")
            try:
                result = retrieval_chain_.invoke({"question": input_text})
                logger.info("Successfully processed question")
                
                if isinstance(result, dict):
                    logger.debug("Result is a dictionary, displaying as table")
                    st.table(pd.DataFrame(result))
                else:
                    logger.debug("Result is not a dictionary, displaying as text")
                    st.write(result)
            except Exception as e:
                logger.error(f"Error processing question: {str(e)}", exc_info=True)
                st.error(f"Error processing question: {str(e)}")

    def run(self):
        """Runs the Streamlit application."""
        logger.info("Running StreamlitApp")
        self.display_sidebar()
        self.display_main_content()

if __name__ == "__main__":
    logger.info("Starting StreamlitApp")
    app = StreamlitApp()
    app.run() 