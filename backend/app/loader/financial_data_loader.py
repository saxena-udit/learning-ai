import io
import os
from typing import List

import requests
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document

from loader.pdf_source import PDFSource
from utils.utils import utils
from utils.logger import get_logger

# Get logger for this module
logger = get_logger("data_loader")


class FinancialDataLoader:
    """
    A class to manage loading, splitting, and storing financial data from PDFs into a vector database.
    """

    def __init__(self, embedding_model_name: str = utils.embedding_model_name, vector_db_base_path: str = utils.vector_db_base_path):
        """
        Initializes the FinancialDataLoader with the specified embedding model and vector database base path.

        Args:
            embedding_model_name (str): The name of the embedding model to use.
            vector_db_base_path (str): The base directory for storing the vector database.
        """
        logger.info(f"Initializing FinancialDataLoader with embedding model: {embedding_model_name}")
        try:
            self.embeddings = GoogleGenerativeAIEmbeddings(model=embedding_model_name)
            self.vector_db_base_path = vector_db_base_path
            self.persist_directory = os.path.join(self.vector_db_base_path, "pdfs")
            os.makedirs(self.persist_directory, exist_ok=True)
            logger.debug(f"Created persist directory: {self.persist_directory}")

            self.db = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings)
            logger.info("Vector database initialized successfully")
                
            self.headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Windows; Windows x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36'}
        except Exception as e:
            logger.error(f"Error initializing FinancialDataLoader: {str(e)}", exc_info=True)
            raise

    def load_and_split_pdf(self, uploaded_file) -> List[Document]:
        """
        Loads a PDF from an uploaded file, splits it into chunks, and returns the chunks.

        Args:
            uploaded_file: The uploaded PDF file.

        Returns:
            List[Document]: A list of Document objects representing the chunks of the PDF.
        """
        filename = getattr(uploaded_file, 'filename', 'uploaded_file')
        logger.info(f"Loading and splitting PDF file: {filename}")
        
        try:
            temp_filename = "temp.pdf"
            logger.debug(f"Writing uploaded file to temporary file: {temp_filename}")
            with open(temp_filename, "wb") as f:
                file_content = uploaded_file.getvalue()
                f.write(file_content)
                logger.debug(f"Wrote {len(file_content)} bytes to {temp_filename}")
            
            logger.debug(f"Loading PDF using PyPDFLoader: {temp_filename}")
            loader = PyPDFLoader(temp_filename)
            documents = loader.load()
            logger.info(f"Loaded {len(documents)} pages from PDF")

            logger.debug(f"Removing temporary file: {temp_filename}")
            os.remove(temp_filename)
            
            logger.debug("Splitting documents into chunks")
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000, chunk_overlap=100
            )
            splits = text_splitter.split_documents(documents)
            logger.info(f"Split PDF into {len(splits)} chunks")
            
            logger.debug(f"Persisting chunks to database for {filename}")
            self.persist_to_db(filename, splits)
            
            return splits
        except Exception as e:
            logger.error(f"Error loading and splitting PDF {filename}: {str(e)}", exc_info=True)
            return []

    def load_pdf_from_url(self, url: str) -> List[Document]:
        """
        Downloads a PDF from a URL, splits it into chunks, and returns the chunks.

        Args:
            url (str): The URL of the PDF to download.

        Returns:
            List[Document]: A list of Document objects representing the chunks of the PDF.
        """
        logger.info(f"Downloading PDF from {url}")
        
        try:
            file_name = url.split("/")[-1]
            logger.debug(f"Target filename: {file_name}")
            
            logger.debug(f"Sending HTTP request to {url}")
            response = requests.get(url=url, headers=self.headers, timeout=120)
            logger.debug(f"Received response with status code: {response.status_code}")
            
            response.raise_for_status()  # Raise an exception for bad status codes
            
            logger.debug(f"Creating in-memory object from response content ({len(response.content)} bytes)")
            on_fly_mem_obj = io.BytesIO(response.content)
            
            logger.debug(f"Writing content to file: {file_name}")
            with open(file_name, "wb") as f:
                f.write(on_fly_mem_obj.getvalue())

            logger.debug(f"Loading PDF using PyPDFLoader: {file_name}")
            loader = PyPDFLoader(file_name)
            documents = loader.load()
            logger.info(f"Loaded {len(documents)} pages from PDF: {file_name}")

            logger.debug(f"Removing temporary file: {file_name}")
            os.remove(file_name)
            
            logger.debug("Splitting documents into chunks")
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000, chunk_overlap=100
            )
            splits = text_splitter.split_documents(documents)
            return splits
        except Exception as e:
            logger.error(f"Error downloading PDF from {url}: {e}", exc_info=True)
            return []

    def load_vector_db(self, date=None, tickers: List[str] = utils.tickers) -> List[str]:
        """
        Loads the vector database by downloading and processing PDFs from URLs.
        
        Args:
            date (date, optional): Date to get quarter PDFs. If None, gets current quarter.
            tickers (List[str], optional): List of ticker symbols to get PDFs for.
            
        Returns:
            List[str]: List of PDF URLs that were processed
        """
        logger.info(f"Loading vector database for tickers: {tickers}")
        if date:
            logger.info(f"Using specific date: {date}")
        
        logger.debug("Fetching PDF sources")
        try:
            pdf_urls = PDFSource().get_results_links(date=date, tickers=tickers)
            logger.info(f"Found {len(pdf_urls)} PDF URLs to process")
            
            successful_urls = []
            for pdf_url in pdf_urls:
                try:
                    logger.info(f"Processing PDF from URL: {pdf_url}")
                    pdf_chunks = self.load_pdf_from_url(pdf_url)
                    
                    if pdf_chunks:
                        logger.info(f"PDF processed successfully: {len(pdf_chunks)} chunks found")
                        self.persist_to_db(pdf_url, pdf_chunks)
                        successful_urls.append(pdf_url)
                    else:
                        logger.warning(f"No chunks found in PDF: {pdf_url}")
                except requests.exceptions.RequestException as e:
                    logger.error(f"Error downloading PDF from {pdf_url}: {str(e)}", exc_info=True)
                except Exception as e:
                    logger.error(f"Error processing PDF from {pdf_url}: {str(e)}", exc_info=True)

            if successful_urls:
                logger.info(f"Successfully processed {len(successful_urls)} out of {len(pdf_urls)} PDFs")
            else:
                logger.warning("Failed to process any PDFs")
                
            return successful_urls
        except Exception as e:
            logger.error(f"Error loading vector database: {str(e)}", exc_info=True)
            return []

    def persist_to_db(self, pdf_url: str, pdf_chunks: List[Document]) -> None:
        """
        Persists the given PDF chunks to the vector database.

        Args:
            pdf_url (str): The URL or file name of the PDF the chunks came from.
            pdf_chunks (List[Document]): The list of PDF chunks to persist.
        """
        if not pdf_chunks:
            logger.warning(f"No chunks to persist for {pdf_url}")
            return
            
        logger.info(f"Persisting {len(pdf_chunks)} chunks to vector database for {pdf_url}")
        
        try:
            logger.debug(f"Adding {len(pdf_chunks)} documents to vector database")
            self.db.add_documents(documents=pdf_chunks)
            logger.info(f"Successfully added chunks to vector database for {pdf_url}")
        except Exception as e:
            logger.error(f"Error persisting chunks to vector database: {str(e)}", exc_info=True)
            
            # Try to create a new database if adding to existing one failed
            try:
                logger.info("Attempting to create new vector database")
                self.db = Chroma.from_documents(
                    documents=pdf_chunks,
                    embedding=self.embeddings,
                    persist_directory=self.persist_directory
                )
                logger.info("Successfully created new vector database")
            except Exception as nested_e:
                logger.error(f"Failed to create new vector database: {str(nested_e)}", exc_info=True)
                raise

    def vector_db_retriever(self) -> List:
        """
        Gets all the vector database retriever instances.

        Returns:
            List: A list of retriever instances.
        """
        logger.info("Getting vector database retrievers")
        
        try:
            # Get all the subdirectories from vector_db_base_path
            if not os.path.exists(self.vector_db_base_path):
                logger.warning(f"Vector database base path does not exist: {self.vector_db_base_path}")
                return []
                
            subdirectories = [f.path for f in os.scandir(self.vector_db_base_path) if f.is_dir()]
            
            if not subdirectories:
                logger.warning(f"No subdirectories found in vector database base path: {self.vector_db_base_path}")
                return []
                
            logger.info(f"Found {len(subdirectories)} vector database directories")
            
            all_retrievers = []
            for persist_directory in subdirectories:
                try:
                    logger.debug(f"Loading vector database from {persist_directory}")
                    db = Chroma(persist_directory=persist_directory, embedding_function=self.embeddings)
                    retriever = db.as_retriever()
                    all_retrievers.append(retriever)
                    logger.debug(f"Successfully loaded retriever from {persist_directory}")
                except Exception as e:
                    logger.error(f"Error loading vector database from {persist_directory}: {str(e)}", exc_info=True)
            
            logger.info(f"Loaded {len(all_retrievers)} vector database retrievers")
            return all_retrievers
        except Exception as e:
            logger.error(f"Error getting vector database retrievers: {str(e)}", exc_info=True)
            return []

    def search_vector_db(self, query: str) -> List[Document]:
        """
        Searches all vector databases for the given query.

        Args:
            query (str): The query to search for.

        Returns:
            List[Document]: A list of Document objects representing the search results.
        """
        logger.info(f"Searching vector databases for query: '{query[:50]}...'")
        
        try:
            # Get all the subdirectories from vector_db_base_path
            if not os.path.exists(self.vector_db_base_path):
                logger.warning(f"Vector database base path does not exist: {self.vector_db_base_path}")
                return []
                
            subdirectories = [f.path for f in os.scandir(self.vector_db_base_path) if f.is_dir()]
            
            if not subdirectories:
                logger.warning(f"No subdirectories found in vector database base path: {self.vector_db_base_path}")
                return []
                
            logger.info(f"Found {len(subdirectories)} vector database directories to search")
            
            all_results = []
            for persist_directory in subdirectories:
                try:
                    logger.debug(f"Searching vector database in {persist_directory}")
                    db = Chroma(persist_directory=persist_directory, embedding_function=self.embeddings)
                    results = db.similarity_search(query)
                    logger.debug(f"Found {len(results)} results in {persist_directory}")
                    all_results.extend(results)
                except Exception as e:
                    logger.error(f"Error searching vector database in {persist_directory}: {str(e)}", exc_info=True)
            
            logger.info(f"Found a total of {len(all_results)} results across all vector databases")
            return all_results
        except Exception as e:
            logger.error(f"Error searching vector databases: {str(e)}", exc_info=True)
            return []

    def format_docs(self, docs: List[Document]) -> str:
        """
        Formats a list of documents into a string.

        Args:
            docs (List[Document]): The list of documents to format.

        Returns:
            str: A formatted string representing the documents.
        """
        logger.debug(f"Formatting {len(docs)} documents")
        
        try:
            formatted = "\n\n".join(doc.page_content for doc in docs)
            logger.debug(f"Successfully formatted {len(docs)} documents into {len(formatted)} characters")
            return formatted
        except Exception as e:
            logger.error(f"Error formatting documents: {str(e)}", exc_info=True)
            return ""

