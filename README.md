# Langchain-Gemini Financial Chatbot

This project implements a chatbot that leverages Langchain, Google's Gemini model, and a vector database to answer questions based on financial documents (PDFs). The project includes both a React frontend and a FastAPI backend for a complete solution.

## Key Features

-   **Context-Aware Chat:** The chatbot uses vector databases built from financial reports to provide contextually relevant answers.
-   **PDF Handling:**
    -   Ingests PDF documents, splits them into chunks, and stores them in a vector database.
    -   Retrieves relevant chunks from the database based on user queries.
    -   Supports loading PDFs from URLs and local uploads.
-   **Multiple Vector Databases:** The system efficiently manages multiple vector databases, each potentially representing a different data source.
-   **Gemini Integration:** Uses Google's Gemini AI models for natural language understanding and generation.
-   **Context Toggle:** Choose whether the chatbot should use vector database context or not.
-   **Multiple Interfaces:** 
    -   React frontend with real-time chat interface
    -   FastAPI backend API
    -   Streamlit application (alternative interface)
-   **Stock Ticker Selection:** Easily switch between different company data
-   **Dynamic PDF Retrieval:** Scrapes Google Search results to find relevant financial report PDFs based on company tickers.
-   **Comprehensive Logging:** Detailed logging system for tracking operations and troubleshooting.

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api.py             # FastAPI implementation
│   │   ├── streamlit_app.py   # Streamlit interface
│   │   ├── app.py             # Core application logic
│   │   ├── chatbot/           # Chatbot implementation
│   │   ├── loader/            # PDF loading and vector DB management
│   │   ├── model/             # LLM model providers
│   │   ├── templates/         # Prompt templates
│   │   └── utils/             # Utility functions
│   ├── chroma_db/             # Vector database storage
│   ├── logs/                  # Application logs
│   ├── tests/                 # Test suite
│   ├── venv/                  # Python virtual environment
│   ├── requirements.txt       # Python dependencies
│   └── .env                   # Environment variables
├── frontend/
│   └── src/                   # React frontend source code
```

## How It Works

1.  **PDF Processing:**
    -   PDFs are uploaded through the UI or fetched from URLs via Google Search.
    -   Documents are split into smaller chunks of text.
    -   Embeddings are generated for each chunk using Google's embedding model.
    -   The chunks and embeddings are stored in a vector database.

2.  **Question Answering:**
    -   User questions are processed by the chatbot.
    -   If context-aware mode is enabled, relevant document chunks are retrieved from the vector database.
    -   The prompt template includes context from the retrieved documents when available.
    -   Google's Gemini model generates a response based on the prompt and context.

3.  **Ticker Symbol Support:**
    -   Users can select specific company tickers.
    -   The system automatically finds and processes relevant financial reports.
    -   Responses are tailored to the selected company's data.

## Setup and Usage

### Backend Setup

1. Create a virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the backend directory with these variables:
```
EMBEDDING_MODEL_NAME=models/embedding-001
MODEL_NAME=gemini-1.5-pro
GOOGLE_API_KEY=your_google_api_key
```

4. Run the API Server:
```bash
cd app
python api.py
```

The API will be available at `http://localhost:8000`

5. Alternatively, run the Streamlit app:
```bash
cd app
streamlit run streamlit_app.py
```

### Frontend Setup

1. Prerequisites:
   - Node.js and npm

2. Install dependencies:
```bash
cd frontend
npm install
```

3. Start the development server:
```bash
npm run dev
```

The frontend application will be available at `http://localhost:3000`

### API Endpoints

1. **POST /ask** - Ask a question to the chatbot
    ```json
    {
        "text": "What was TCS's revenue in Q1?",
        "context_aware": true,
        "ticker": "TCS"
    }
    ```

2. **POST /upload-pdf** - Upload a PDF file to add to the context
    - Form data: `file`: PDF file

3. **POST /add-ticker-context** - Add context from ticker symbols
    ```json
    {
        "tickers": ["RELIANCE", "TCS"]
    }
    ```

4. **GET /health** - Check API health status

## Technologies Used

- **Backend**:
  - FastAPI
  - Langchain
  - Google Gemini AI models
  - ChromaDB for vector database storage
  - Python

- **Frontend**:
  - React
  - TypeScript
  - CSS

## Future Improvements

-   **Database Management:** Implement mechanisms to remove old or irrelevant databases.
-   **Additional Data Sources:** Support more sources like CSV, TXT, etc.
-   **Authentication:** Add user authentication and authorization.
-   **Improved Error Handling:** Enhance error handling and recovery mechanisms.
-   **Performance Optimization:** Improve vector search and response generation speed.
-   **Enhanced UI:** Add visualization tools for financial data.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

## License

This project is licensed under the MIT license.
