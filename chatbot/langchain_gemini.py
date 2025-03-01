from langchain_core.prompts import ChatPromptTemplate

from langchain_core.output_parsers import JsonOutputParser, StrOutputParser

from langchain_google_genai import ChatGoogleGenerativeAI

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

import os

from dotenv import load_dotenv

load_dotenv()

model_name="gemini-1.5-pro"

os.environ["LANGCHAIN_TRACING_V2"]="true"
os.environ["LANGSMITH_PROJECT"]="Finance Chatbot-{model_name}".format(model_name=model_name)

if "LANGCHAIN_API_KEY" not in os.environ:
    os.environ["LANGCHAIN_API_KEY"]=os.getenv("LANGCHAIN_API_KEY")

if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")


## Load PDF and prepare context
def load_and_split_pdf(uploaded_file):
    """Loads a PDF from an uploaded file, splits it into chunks, and returns the chunks."""
    try:
        with open("temp.pdf", "wb") as f:
            f.write(uploaded_file.getvalue())
        loader = PyPDFLoader("temp.pdf")
        documents = loader.load()

        os.remove("temp.pdf")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=100
        )
        splits = text_splitter.split_documents(documents)
        return splits
    except Exception as e:
        return []


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


## Prompt Template with conditional context
def create_prompt_template(has_context):
    if has_context:
        system_prompt_template = """
        You are a knowledgeable financial advisor. 
        Answer the user's questions based on the provided context.
        The user might ask for financial data in a table format. If so, extract all the relevant financial information from the context.
        Do not limit the financial information to just stock name, current price, etc.
        Include any relevant financial data points like YOY growth, revenue by business segment, etc.
        Structure the output as a JSON object. 
        Each entry in the JSON should be a key-value pair of financial data points.
        If any field is not found in the context, do not include that field in the result.
        If multiple stocks or financial entities are in context, add them as separate entries.
        
        Context:
        {context}
        """
    else:
        system_prompt_template = """
        You are a knowledgeable financial advisor. 
        Answer the user's questions to the best of your ability.
        The user might ask for financial data in a table format. If so, generate the table with relevant financial information.
        Do not limit the financial information to just stock name, current price, etc.
        Include any relevant financial data points like YOY growth, revenue by business segment, etc.
        Structure the output as a JSON object. 
        Each entry in the JSON should be a key-value pair of financial data points.
        If any field is not found or is not applicable, do not include that field in the result.
        If multiple stocks or financial entities are asked add them as separate entries.
        """

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt_template),
            ("user", "Question:{question}"),
        ]
    )
    return prompt


# ollama LLAma2 LLm 
llm= ChatGoogleGenerativeAI(
    model=model_name,
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    # other params...
)

json_output_parser = JsonOutputParser()
output_parser = StrOutputParser()

def parser():
    return output_parser

# Adding context to the chain.
def retrieval_chain(prompt, retriever, uploaded_file):
    # Adding context to the chain.
    if uploaded_file:
        
        retrieval_chain = {
            "context": lambda x: format_docs(retriever),
            "question": lambda x: x["question"]
        } | prompt | llm | parser()
    else:

        retrieval_chain = {
            "question": lambda x: x["question"]
        } | prompt | llm | parser()
    return retrieval_chain
    
# go to https://www.nseindia.com/market-data/live-equity-market?symbol=NIFTY%2050 and find first 3 stocks
