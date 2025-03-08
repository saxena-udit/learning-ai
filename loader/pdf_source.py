from utils import get_financial_quarter, tickers
from googlesearch import search
import logging

logger = logging.getLogger(__name__)


def get_results_links(date:None): 
    financial_quarter = get_financial_quarter(date)
    results = []
    for ticker in tickers:
        query = f"{ticker} {financial_quarter} filetype:pdf"
        print(f"Searching for {query}...\n")
        for url in search(query, tld="co.in", num=3, stop=2, pause=2):
            results.append(url)
    logger.info(f"Found {len(results)} PDFs for {financial_quarter}.")
    return results
