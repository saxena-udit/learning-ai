import streamlit as st
import pandas as pd
from chatbot.langchain_gemini import create_prompt_template, retrieval_chain
from loader.financial_data_loader import load_and_split_pdf
from utils import model_name
# Set the page configuration to use full width
st.set_page_config(page_title=f'Langchain Demo [model:{model_name}]', layout="wide")

CONTEXT_AWARE_KEY = "context_aware"

# Create columns for layout
col1, col2 = st.columns([1, 3])  # Adjust column width ratio as needed

if CONTEXT_AWARE_KEY not in st.session_state:
    st.session_state[CONTEXT_AWARE_KEY] = True

def flip_context_aware():
    st.session_state[CONTEXT_AWARE_KEY] = not st.session_state[CONTEXT_AWARE_KEY]

# File uploader in the left column
with col1:
    st.checkbox(
    "Context Aware", value=st.session_state[CONTEXT_AWARE_KEY], key="check", on_change=flip_context_aware)

    uploaded_file = st.file_uploader("Add more context", type="pdf")

    if uploaded_file:
        load_and_split_pdf(uploaded_file)

# Main content in the right column
with col2:

    retrieval_chain_ = retrieval_chain(st.session_state[CONTEXT_AWARE_KEY])

    input_text=st.text_input("Question:")

    if input_text:
        result = retrieval_chain_.invoke({"question": input_text})

        if isinstance(result,dict):
            st.table(pd.DataFrame(result))
        else:
            st.write(f"Generating plain text with {create_prompt_template(st.session_state[CONTEXT_AWARE_KEY])}")
            st.write(result)