import io
import logging
import os
from typing import List

import requests
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document

from loader.pdf_source import PDFSource
from utils import vector_db_base_path, embedding_model_name, tickers

logger = logging.getLogger(__name__)


class FinancialDataLoader:
    """
    A class to manage loading, splitting, and storing financial data from PDFs into a vector database.
    """

    def __init__(self, embedding_model_name: str = embedding_model_name, vector_db_base_path: str = vector_db_base_path):
        """
        Initializes the FinancialDataLoader with the specified embedding model and vector database base path.

        Args:
            embedding_model_name (str): The name of the embedding model to use.
            vector_db_base_path (str): The base directory for storing the vector database.
        """
        self.embeddings = GoogleGenerativeAIEmbeddings(model=embedding_model_name)
        self.vector_db_base_path = vector_db_base_path
        self.persist_directory = os.path.join(self.vector_db_base_path, "pdfs")
        os.makedirs(self.persist_directory, exist_ok=True)

        self.db = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings)
            
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Windows; Windows x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36'}

    def load_and_split_pdf(self, uploaded_file) -> List[Document]:
        """
        Loads a PDF from an uploaded file, splits it into chunks, and returns the chunks.

        Args:
            uploaded_file: The uploaded PDF file.

        Returns:
            List[Document]: A list of Document objects representing the chunks of the PDF.
        """
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
            self.persist_to_db( "temp.pdf", splits)
            return splits
        except Exception as e:
            logger.error(f"Error loading and splitting PDF: {e}", exc_info=True)
            return []

    def load_pdf_from_url(self, url: str) -> List[Document]:
        """
        Downloads a PDF from a URL, splits it into chunks, and returns the chunks.

        Args:
            url (str): The URL of the PDF to download.

        Returns:
            List[Document]: A list of Document objects representing the chunks of the PDF.
        """
        logger.info(f"Downloading PDF from {url}...")
        file_name = url.split("/")[-1]
        response = requests.get(url=url, headers=self.headers, timeout=120)
        response.raise_for_status()  # Raise an exception for bad status codes
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

    def load_vector_db(self, date=None,tickers: List[str] = tickers) -> None:
        """
        Loads the vector database by downloading and processing PDFs from URLs.
        
        Args:
            date(date): pass date to get quarter pdfs, by default None and gets current quarter
        """
        pdf_urls = PDFSource().get_results_links(date=date,tickers=tickers)

        for pdf_url in pdf_urls:
            try:
                pdf_chunks = self.load_pdf_from_url(pdf_url)
                logger.info(
                    f"PDF downloaded and split successfully. {len(pdf_chunks)} chunks found.")

                self.persist_to_db(pdf_url, pdf_chunks)
            except requests.exceptions.RequestException as e:
                logger.error(
                    f"Error downloading PDF from {pdf_url}: {e}", exc_info=True
                )
            except Exception as e:
                logger.error(
                    f"Error processing PDF from {pdf_url}: {e}", exc_info=True
                )

        logger.info(f"PDFs {",".join(pdf_urls)} downloaded and split successfully.")
        return pdf_urls

    def persist_to_db(self, pdf_url: str, pdf_chunks: List[Document]) -> None:
        """
        Persists the given PDF chunks to the vector database.

        Args:
            pdf_url (str): The URL or file name of the PDF the chunks came from.
            pdf_chunks (List[Document]): The list of PDF chunks to persist.
        """
        
        try:
            self.db.add_documents(documents=pdf_chunks)
        except Exception as e:
            logger.info(f"No existing DB found. Creating new DB.",exc_info=True)
            self.db = Chroma.from_documents(
                documents=pdf_chunks,
                embedding=self.embeddings,
                persist_directory=self.persist_directory,
            )

        logger.info(
            f"Chunks from {pdf_url} loaded into vector DB: {self.persist_directory}"
        )

    def vector_db_retriever(self) -> List:
        """
        Gets all the vector database retriever instances.

        Returns:
            List: A list of retriever instances.
        """
        # get all the subdirectories from vector_db_base_path
        subdirectories = [f.path for f in os.scandir(self.vector_db_base_path) if f.is_dir()]
        all_retrievers = []
        for persist_directory in subdirectories:
            logger.info(f"Loading vector database from {persist_directory}")
            db = Chroma(persist_directory=persist_directory, embedding_function=self.embeddings)
            retriever = db.as_retriever()
            all_retrievers.append(retriever)
        return all_retrievers

    def search_vector_db(self, query: str) -> List[Document]:
        """
        Searches all vector databases for the given query.

        Args:
            query (str): The query to search for.

        Returns:
            List[Document]: A list of Document objects representing the search results.
        """
        # get all the subdirectories from vector_db_base_path
        subdirectories = [f.path for f in os.scandir(self.vector_db_base_path) if f.is_dir()]
        all_results = []
        for persist_directory in subdirectories:
            logger.info(f"Loading vector database from {persist_directory}")
            db = Chroma(persist_directory=persist_directory, embedding_function=self.embeddings)
            all_results.extend(db.similarity_search(query))
        return all_results

    def format_docs(self, docs: List[Document]) -> str:
        """
        Formats a list of documents into a string.

        Args:
            docs (List[Document]): The list of documents to format.

        Returns:
            str: A formatted string representing the documents.
        """
        return "\n\n".join(doc.page_content for doc in docs)

