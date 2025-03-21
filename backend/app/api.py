import logging
import os
from fastapi import FastAPI, UploadFile, File, Form, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import time
from pathlib import Path

from chatbot.financial_chatbot import financial_chatbot
from loader.financial_data_loader import financial_data_loader
from utils.utils import utils
from utils.logger import setup_logger

# Configure logger for this module
logger = setup_logger("api")

# Remove existing basic logging configuration
# Create logs directory if it doesn't exist
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "api.log"

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
    chatbot = financial_chatbot
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
    request_id = int(time.time() * 1000)  # Simple request ID based on timestamp
    logger.info(f"Request {request_id} started | Path: {request.url.path} | Method: {request.method}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(
            f"Request {request_id} completed | Path: {request.url.path} | Method: {request.method} | "
            f"Status: {response.status_code} | Time: {process_time:.3f}s"
        )
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"Request {request_id} failed | Path: {request.url.path} | Method: {request.method} | "
            f"Error: {str(e)} | Time: {process_time:.3f}s",
            exc_info=True
        )
        raise

@app.post("/ask")
async def ask_question(question: Question):
    logger.info(f"Processing question: '{question.text[:50]}...' | Context aware: {question.context_aware} | Ticker: {question.ticker}")
    
    try:
        if question.ticker:
            logger.debug(f"Loading vector DB for ticker: {question.ticker}")
            financial_data_loader.load_vector_db(tickers=[question.ticker])
        
        retrieval_chain = chatbot.retrieval_chain(question.context_aware)
        logger.debug("Invoking retrieval chain")
        result = retrieval_chain.invoke({"question": question.text})
        logger.info("Successfully processed question")
        
        return {"response": result}
    except Exception as e:
        logger.error(f"Error processing question: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF file to add to the context
    """
    if not file.filename.lower().endswith('.pdf'):
        logger.warning(f"Invalid file type received: {file.filename}")
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    logger.info(f"Received PDF upload: {file.filename}")
    try:
        contents = await file.read()
        if not contents:
            logger.warning(f"Empty PDF file received: {file.filename}")
            raise HTTPException(status_code=400, detail="Empty file")
            
        logger.debug(f"Processing PDF file: {file.filename} | Size: {len(contents)} bytes")
        splits = financial_data_loader.load_and_split_pdf(file)
        if not splits:
            logger.warning(f"Could not process PDF file: {file.filename}")
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
        logger.warning("Add ticker context called with no tickers")
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
            logger.error("Health check failed: Core components not initialized")
            raise HTTPException(status_code=500, detail="Core components not initialized")
        logger.debug("Health check requested and passed")
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