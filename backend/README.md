# Finance Chatbot Backend

This is the backend service for the Finance Chatbot application. It provides API endpoints for chat functionality and financial data processing.

## Architecture

### NSE Data Handling
The NSE (National Stock Exchange) data handling is split into two components for better separation of concerns:

- **`NSEIndexes`** (`app/nse/nse_indexes.py`): Handles raw data fetching, caching, and data processing
- **`NSEFormatter`** (`app/nse/nse_formatter.py`): Handles data formatting, column configuration, and display logic

This separation allows for:
- Clean data handling without formatting concerns
- Reusable formatting logic
- Better maintainability and testing
- Optimized performance with focused responsibilities

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env_my` file with the following variables:
```
EMBEDDING_MODEL_NAME=models/embedding-001
MODEL_NAME=gemini-1.5-pro
LANGCHAIN_API_KEY=your_langchain_api_key
GOOGLE_API_KEY=your_google_api_key
```

## Running the Server

Start the FastAPI server:
```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

## Streamlit Application

The application also includes a Streamlit web interface with two main tabs:

### Running the Streamlit App

Start the Streamlit application:
```bash
streamlit run app/streamlit_app.py --server.port 8501
```

The web interface will be available at `http://localhost:8501`

### Tab Structure

1. **📈 NSE Indexes Tab**: 
   - Displays real-time NSE (National Stock Exchange) index data
   - Features filtering by index type and sub-type
   - **Native column visibility**: Use the view icon (👁️) in the dataframe to show/hide columns
   - **Available columns**: Index, Value, Change %, 52W High, 52W Low, Down from High %, Up from Low %, Variation, High, Low, Open, Prev Close, Time, Index Type, Index Sub Type
   - Shows comprehensive market data including:
     - Current values and percentage changes
     - 52-week highs and lows
     - Distance from highs and lows
   - Includes summary statistics and refresh functionality

2. **🤖 Financial Chatbot Tab**:
   - Interactive chat interface for financial queries
   - Context-aware responses based on uploaded documents
   - Support for PDF document uploads
   - Ticker symbol input for specific stock analysis
   - Real-time question processing and response display
   - **Sidebar controls**: Context-aware toggle, file uploader, and ticker input are integrated within this tab

### Features

- **Real-time Data**: NSE indexes are updated every 5 minutes
- **Interactive Filtering**: Filter indexes by type and sub-type
- **Document Upload**: Add PDF documents for context-aware responses
- **Ticker Analysis**: Input specific ticker symbols for targeted analysis
- **Responsive Design**: Clean, modern interface with proper data formatting

## API Endpoints

- `GET /`: Health check endpoint
- `GET /tickers`: Get list of available tickers
- `POST /chat`: Send a chat message
  - Request body:
    ```json
    {
      "message": "string",
      "ticker": "string" // optional
    }
    ```
- `POST /extract-tickers`: Extract ticker symbols from a question using LLM
  - Request body:
    ```json
    {
      "text": "string"
    }
    ```
  - Response:
    ```json
    {
      "tickers": ["AAPL", "MSFT"] // array of extracted ticker symbols
    }
    ```
- `POST /ask`: Ask a question to the financial chatbot
  - Now supports automatic ticker extraction from questions
  - Provides context-aware responses based on financial data
  - Integrates ticker extraction directly into vector database search
  - Prioritizes explicitly provided ticker symbols over extracted ones