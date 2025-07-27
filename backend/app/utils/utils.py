import datetime
import os
from dotenv import load_dotenv
from app.utils.logger import get_logger

# Get a logger for this module
logger = get_logger("utils")

class Utils:
    def __init__(self):
        # Load environment variables first
        load_dotenv(verbose=True, override=True, dotenv_path=".env_my")
        
        self.vector_db_base_path = "./chroma_db/"
        self.embedding_model_name = os.getenv("EMBEDDING_MODEL_NAME", "models/embedding-001")  # Load from env with default
        self.model_name = os.getenv("MODEL_NAME", "gemini-1.5-pro")  # Default to gemini-1.5-pro if not set
        self.tickers = ["RELIANCE", "TCS"]
        logger.info(f"Initialized with model name: {self.model_name}")
        
    def load_env_vars(self):
        """Load environment variables needed for the application"""
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGSMITH_PROJECT"] = f"Finance Chatbot-{self.model_name}"

        try:
            os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
            if not os.environ["LANGCHAIN_API_KEY"]:
                logger.warning("LANGCHAIN_API_KEY is empty")
            else:
                logger.info("LANGCHAIN_API_KEY loaded successfully")
            
            os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
            if not os.environ["GOOGLE_API_KEY"]:
                logger.warning("GOOGLE_API_KEY is empty")
            else:
                logger.info("GOOGLE_API_KEY loaded successfully")
        except Exception as e:
            logger.error(f"Error loading environment variables: {str(e)}", exc_info=True)

    @staticmethod
    def get_financial_quarter(date=None):
        """
        Determines the financial quarter for a given date (or the current date if none is provided).

        Args:
            date (datetime.date, optional): The date to determine the financial quarter for. 
                                             Defaults to the current date.

        Returns:
            str: A string representing the financial quarter (e.g., "Q1", "Q2", "Q3", "Q4") and the year.
        """
        if date is None:
            date = datetime.date.today()

        year = date.year
        month = date.month

        if month in [4, 5, 6]:
            quarter = "Q1"
        elif month in [7, 8, 9]:
            quarter = "Q2"
        elif month in [10, 11, 12]:
            quarter = "Q3"
        else:  # month in [1, 2, 3]
            quarter = "Q4"
            year -= 1  # Adjusting year for last quarter

        return f"{quarter} FY{year}-{year+1}"

# Initialize utils instance
utils = Utils()
utils.load_env_vars()