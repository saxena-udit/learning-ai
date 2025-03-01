import streamlit as st
import pandas as pd
from langchain_gemini import model_name,load_and_split_pdf, create_prompt_template, retrieval_chain

# Set the page configuration to use full width
st.set_page_config(page_title=f'Langchain Demo [model:{model_name}]', layout="wide")

# Create columns for layout
col1, col2 = st.columns([1, 3])  # Adjust column width ratio as needed

# File uploader in the left column
with col1:
    uploaded_file = st.file_uploader("Context file", type="pdf")

# Main content in the right column
with col2:
    # Create pdf chunks
    pdf_chunks = []

    if uploaded_file:
        pdf_chunks = load_and_split_pdf(uploaded_file)
        retriever = pdf_chunks
        prompt = create_prompt_template(has_context=True)
        retrieval_chain_ = retrieval_chain(prompt, retriever,uploaded_file)

    else:
        prompt = create_prompt_template(has_context=False)
        retrieval_chain_ = retrieval_chain(prompt, retriever=[], uploaded_file=None)


    input_text=st.text_input("Question:")

    if input_text:
        result = retrieval_chain_.invoke({"question": input_text})

        if isinstance(result,dict):
            st.table(pd.DataFrame(result))
        else:
            st.write("Generating plain text")
            st.write(result)