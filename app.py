import streamlit as st
import pandas as pd
from chatbot.langchain_gemini import LangchainGeminiChatbot
from loader.financial_data_loader import FinancialDataLoader
from utils import model_name

class StreamlitApp:
    def __init__(self):
        # Initialize Streamlit settings
        st.set_page_config(page_title=f'Langchain Demo [model:{model_name}]', layout="wide")
        self.context_aware_key = "context_aware"

        # Initialize session state
        if self.context_aware_key not in st.session_state:
            st.session_state[self.context_aware_key] = True

        # Initialize LangchainGeminiChatbot
        self.chatbot = LangchainGeminiChatbot()
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
                st.write(f"Generating plain text with {self.chatbot.create_prompt_template(st.session_state[self.context_aware_key])}")
                st.write(result)


    def run(self):
        """Runs the Streamlit application."""
        self.display_sidebar()
        self.display_main_content()


if __name__ == "__main__":
    app = StreamlitApp()
    app.run()
