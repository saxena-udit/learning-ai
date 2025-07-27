import streamlit as st
from app.utils.utils import utils
from app.utils.logger import get_logger
import uvicorn
import multiprocessing
import os
import sys
import argparse

# Setup logger for this module
logger = get_logger("main")

def parse_arguments():
    """Parse command line arguments for port configuration"""
    parser = argparse.ArgumentParser(description="Run the financial chatbot application")
    parser.add_argument("--fastapi-port", type=int, default=8002, help="Port for FastAPI server (default: 8002)")
    parser.add_argument("--streamlit-port", type=int, default=8502, help="Port for Streamlit server (default: 8502)")
    return parser.parse_args()

def run_fastapi(port=8000):
    """Run the FastAPI server"""
    logger.info(f"Starting FastAPI server on port {port}")
    uvicorn.run("app.api:app", host="0.0.0.0", port=port, reload=True)

def run_streamlit(port=8500):
    """Run the Streamlit server"""
    logger.info(f"Starting Streamlit server on port {port}")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    streamlit_path = os.path.join(current_dir, "app", "streamlit_app.py")
    os.system(f"{sys.executable} -m streamlit run {streamlit_path} --server.port {port}")

if __name__ == "__main__":
    logger.info("Initializing application servers")
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Start both servers in separate processes
    fastapi_process = multiprocessing.Process(target=run_fastapi, args=(args.fastapi_port,))
    streamlit_process = multiprocessing.Process(target=run_streamlit, args=(args.streamlit_port,))

    # Start the processes
    logger.info("Starting server processes")
    fastapi_process.start()
    streamlit_process.start()

    try:
        # Wait for both processes to complete
        logger.info("Server processes started, waiting for completion")
        fastapi_process.join()
        streamlit_process.join()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down servers...")
        fastapi_process.terminate()
        streamlit_process.terminate()
        fastapi_process.join()
        streamlit_process.join()
        logger.info("Servers shut down successfully")
