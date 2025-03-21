import logging
import os
from fastapi import FastAPI, UploadFile, File, Form, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import time
from pathlib import Path

from chatbot.financial_chatbot import FinancialChatbot
from loader.financial_data_loader import FinancialDataLoader
from utils import utils

# Create logs directory if it doesn't exist
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "api.log"

# Configure logging with try-except to handle permission issues
try:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file)
        ]
    )
except Exception as e:
    # Fallback to console-only logging if file logging fails
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    print(f"Warning: Could not set up file logging: {e}")

logger = logging.getLogger(__name__)

app = FastAPI(title=f'Financial Chatbot API [model:{utils.model_name}]')

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize global instances with error handling
try:
    logger.info("Initializing chatbot and financial data loader...")
    chatbot = FinancialChatbot()
    financial_data_loader = FinancialDataLoader()
    logger.info("Initialization complete")
except Exception as e:
    logger.error(f"Failed to initialize components: {str(e)}", exc_info=True)
    raise RuntimeError(f"Failed to initialize API components: {str(e)}")

class Question(BaseModel):
    text: str
    context_aware: bool = True
    ticker: Optional[str] = None

class TickerRequest(BaseModel):
    tickers: List[str]

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log all requests and their processing time"""
    start_time = time.time()
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(
            f"Path: {request.url.path} | Method: {request.method} | "
            f"Status: {response.status_code} | Time: {process_time:.3f}s"
        )
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"Request failed - Path: {request.url.path} | Method: {request.method} | "
            f"Error: {str(e)} | Time: {process_time:.3f}s"
        )
        raise

@app.post("/ask")
async def ask_question(question: Question):
    if question.ticker:
        financial_data_loader.load_vector_db(tickers=[question.ticker])
    
    retrieval_chain = chatbot.retrieval_chain(question.context_aware)
    result = retrieval_chain.invoke({"question": question.text})
    
    return {"response": result}

@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF file to add to the context
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    logger.info(f"Received PDF upload: {file.filename}")
    try:
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="Empty file")
            
        splits = financial_data_loader.load_and_split_pdf(file)
        if not splits:
            raise HTTPException(status_code=400, detail="Could not process PDF file")
            
        logger.info(f"Successfully processed PDF {file.filename} with {len(splits)} chunks")
        return {"message": f"Successfully processed PDF with {len(splits)} chunks"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing PDF {file.filename}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

@app.post("/add-ticker-context")
async def add_ticker_context(request: TickerRequest):
    """
    Add context from ticker symbols
    """
    if not request.tickers:
        raise HTTPException(status_code=400, detail="No tickers provided")
        
    logger.info(f"Adding context for tickers: {request.tickers}")
    try:
        urls = financial_data_loader.load_vector_db(tickers=request.tickers)
        logger.info(f"Successfully loaded {len(urls)} PDFs for tickers: {request.tickers}")
        return {"message": f"Loaded {len(urls)} PDFs for tickers: {', '.join(request.tickers)}"}
    except Exception as e:
        logger.error(f"Error loading ticker context: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error loading ticker context: {str(e)}")

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    try:
        # Verify core components are working
        if not chatbot or not financial_data_loader:
            raise HTTPException(status_code=500, detail="Core components not initialized")
        logger.debug("Health check requested")
        return {"status": "healthy"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Service unhealthy")

if __name__ == "__main__":
    logger.info("Starting FastAPI application...")
    try:
        uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}", exc_info=True) 