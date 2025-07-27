from app.utils.utils import utils
from googlesearch import search
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class PDFSource:
    """
    A class to manage searching for and retrieving financial PDF links from Google.
    """

    def __init__(self):
        """
        Initializes the PDFSource with a list of tickers.
        """

    def get_results_links(self,tickers: List[str], date: Optional[str] = None) -> List[str]:
        """
        Searches Google for financial PDFs for the given tickers and financial quarter.

        Args:
            date (Optional[str]): An optional date string to determine the financial quarter.
                                  If None, the current quarter is used.

        Returns:
            List[str]: A list of URLs to financial PDFs found in the search results.
        """
        financial_quarter = utils.get_financial_quarter(date)
        results = []
        for ticker in tickers:
            query = f"{ticker} {financial_quarter} filetype:pdf"
            logger.info(f"Searching for {query}...")
            try:
                for url in search(query, tld="co.in", num=3, stop=2, pause=2):
                    results.append(url)
            except Exception as e:
                logger.error(f"Error during Google search for query '{query}': {e}")
        logger.info(f"Found {len(results)} PDFs for {financial_quarter}.")
        return results
