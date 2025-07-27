# Finance Chatbot Backend

This is the backend service for the Finance Chatbot application. It provides API endpoints for chat functionality and financial data processing.

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
