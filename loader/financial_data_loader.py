import io
import logging
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os

from langchain_google_genai import GoogleGenerativeAIEmbeddings
import requests


from loader.pdf_source import get_results_links

from utils  import vector_db_base_path,embedding_model_name

import logging

logger = logging.getLogger(__name__)

embeddings = GoogleGenerativeAIEmbeddings(model=embedding_model_name)


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
        persist_to_db(embeddings, "temp.pdf", splits)
        return splits
    except Exception as e:
        logger.error(f"Error loading and splitting PDF: {e}",e)
        return []


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

headers = {'User-Agent': 'Mozilla/5.0 (X11; Windows; Windows x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36'}

def load_pdf_from_url(url):
    logger.info(f"Downloading PDF from {url}...")
    file_name = url.split("/")[-1]
    response = requests.get(url=url, headers=headers, timeout=120)
    on_fly_mem_obj = io.BytesIO(response.content)
    with open(file_name, "wb") as f:
        f.write(on_fly_mem_obj.getvalue())
    
    loader = PyPDFLoader(file_name)
    documents = loader.load()

    os.remove(file_name)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=100
    )
    splits = text_splitter.split_documents(documents)
    return splits


def load_vector_db():
    """Loads the vector database from the specified file."""
    pdf_urls = get_results_links(date=None)

    for pdf_url in pdf_urls:
        try:
            pdf_chunks = load_pdf_from_url(pdf_url)
            logger.info(f"PDF downloaded and split successfully. {len(pdf_chunks)} chunks found.")

            persist_to_db(embeddings, pdf_url, pdf_chunks)
            
        except Exception as e:
                logger.error(
                    f"Error downloading or processing PDF from {pdf_url}: {e}"
                )
    logger.info("PDFs downloaded and split successfully.")

def persist_to_db(embeddings, pdf_url, pdf_chunks):
    persist_directory = os.path.join(vector_db_base_path, "pdfs")
    os.makedirs(persist_directory, exist_ok=True)
    try:
        db = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
        logger.info(f"Existing DB found. Adding new documents.")
        db.add_documents(documents=pdf_chunks)
        db.persist()
    except FileNotFoundError:
        logger.info(f"No existing DB found. Creating new DB.")
        Chroma.from_documents(
                    documents=pdf_chunks,
                    embedding=embeddings,
                    persist_directory=persist_directory,
                )
            
    logger.info(
                f"Chunks from {pdf_url} loaded into vector DB: {persist_directory}"
            )

def vector_db_retriever():
     #get all the subdirectories from vector_db_base_path
    subdirectories = [f.path for f in os.scandir(vector_db_base_path) if f.is_dir()]
    all_retrievers = []
    for persist_directory in subdirectories:
        logger.info(f"Loading vector database from {persist_directory}")
        db = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
        retriever = db.as_retriever()
        all_retrievers.append(retriever)
    return all_retrievers

def search_vector_db(query):
     #get all the subdirectories from vector_db_base_path
    subdirectories = [f.path for f in os.scandir(vector_db_base_path) if f.is_dir()]
    all_results = []
    for persist_directory in subdirectories:
        logger.info(f"Loading vector database from {persist_directory}")
        db = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
        all_results.extend(db.similarity_search(query))    
    return all_results