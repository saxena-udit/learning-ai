import logging
import logging.handlers
import os
from pathlib import Path

def setup_logger(name=None, level=logging.INFO):
    """
    Set up a logger with file and console handlers.
    
    Args:
        name (str, optional): Logger name. If None, returns the root logger.
        level (int, optional): Logging level. Defaults to logging.INFO.
        
    Returns:
        logging.Logger: Configured logger
    """
    # Get logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates when called multiple times
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # File handler with rotation
    log_file = log_dir / f"{name if name else 'app'}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, 
        maxBytes=10485760,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    
    # Set formatter for both handlers
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def get_logger(name=None):
    """
    Get a logger. Creates a new one if it doesn't exist.
    
    Args:
        name (str, optional): Logger name.
        
    Returns:
        logging.Logger: Logger instance
    """
    logger = logging.getLogger(name)
    
    # If the logger doesn't have handlers, set it up
    if not logger.hasHandlers():
        return setup_logger(name)
    
    return logger 