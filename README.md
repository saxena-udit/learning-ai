# Langchain-Gemini Financial Chatbot

This project implements a chatbot that leverages Langchain, Google's Gemini model, and a vector database to answer questions based on financial documents (PDFs). The project includes both a Streamlit web interface and a FastAPI backend for programmatic access.

## Key Features

-   **Context-Aware Chat:** The chatbot can use a vector database built from financial reports to provide contextually relevant answers.
-   **PDF Handling:**
    -   Ingests PDF documents, splits them into chunks, and stores them in a vector database.
    -   Retrieves relevant chunks from the database based on user queries.
    -   Supports loading PDF's from URL's and local.
-   **Multiple Vector Databases:**  The system now efficiently manages multiple vector databases, each potentially representing a different data source (e.g., different financial periods or companies).
-   **Gemini Integration:** Uses Google's Gemini model for natural language understanding and generation.
-   **Context Awareness:** Chatbot will be context aware or not depending on your preferences.
-   **Multiple Interfaces:** 
    -   Streamlit UI for user-friendly interactions
    -   FastAPI backend for programmatic access
-   **Dynamic PDF Retrieval:** Scrapes Google Search results to find relevant financial report PDFs based on company tickers and financial quarters.

## Vector Database Enhancements

The latest updates significantly improve how the project handles the vector database.

### Multiple Vector Database Support

-   **Directory-Based Organization:** Instead of a single, monolithic database, the system now stores data in multiple directories within the `vector_db_base_path`. Each subdirectory represents a distinct set of documents (e.g., different financial quarter reports).
-   **Dynamic Loading:** The system now dynamically loads all vector databases found in the `vector_db_base_path` subdirectories. This allows for easy addition of new data without manual reconfiguration.
-   **Unified Search:** When a user asks a question, the `search_vector_db` function efficiently searches across *all* loaded vector databases to find the most relevant documents.
- **Auto creating**: Now, the system will auto generate vector database if none is found.
- **Auto adding:** Now, the system will add documents to existing database when new document is uploaded.

### How it Works

1.  **PDF Loading:**
    -   When a new PDF is uploaded (via the Streamlit UI) or downloaded from the web (using `load_pdf_from_url`):
        -   The PDF is split into smaller chunks of text.
        -   Embeddings are generated for each chunk using the `GoogleGenerativeAIEmbeddings` model.
        -   The chunks and their embeddings are stored in a new vector database inside a subdirectory. If the vector db exists, the chunks are added to the existing DB.
2.  **Database Loading:**
    -   The `load_vector_db` function will auto populate the DB with the PDFs found via Google Search, if no DB is found.
    - The `vector_db_retriever` function now automatically discovers and loads all the vector databases from the subdirectories.
3.  **Question Answering:**
    -   The `search_vector_db` function takes the user's question and performs a similarity search across all loaded databases.
    -   The results from all databases are combined, providing a broader and more relevant context for the language model.
    - The `retrieval_chain` function, will take care of adding the context to the prompt template.

### Code Highlights

-   **`loader/financial_data_loader.py`**
    -   `load_and_split_pdf`: Persists PDF data into a directory specific database.
    -   `load_pdf_from_url`: Handles downloading and processing PDFs from URLs.
    -   `load_vector_db`: Iterates through found URLs, downloads the files and call the persist_to_db
    -   `persist_to_db`: Will persist all the pdf chunks into a DB.
    -   `vector_db_retriever`: Loads all the vector databases, by iterating into the sub directories.
    -   `search_vector_db`: Searches across multiple vector databases for relevant documents.
-   **`chatbot/langchain_gemini.py`**
    -   `retrieval_chain`:  will add context, if there is any.
- **`app.py`**:
    - `Context aware` checkbox will allow user to decide if use vector DB as a context or not.

## Setup and Usage

### Option 1: Streamlit Interface

1.  **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

2.  **Environment Variables:**
    Create a `.env_my` file at the root of the project with these variables:

    ```
    GOOGLE_API_KEY=your_google_api_key
    LANGCHAIN_API_KEY=your_langchain_api_key
    ```
    Remember to use this file when starting the app.

3. **Populate DB:**
    You can run the `app_loader.py` to populate the DB from the PDFs found in google.
    ```
    python app_loader.py
    ```
4.  **Run the Streamlit App:**

    ```bash
    streamlit run app.py
    ```
5.  **Interact:**
    Upload a new pdf or, start asking questions.

### Option 2: API Interface

1. Follow the same setup steps for dependencies and environment variables as above.

2. **Run the API:**
    ```bash
    python api.py
    ```
    Or using uvicorn directly:
    ```bash
    uvicorn api:app --host 0.0.0.0 --port 8000 --reload
    ```

3. **Access API Documentation:**
    - Swagger UI: http://localhost:8000/docs
    - ReDoc: http://localhost:8000/redoc

#### API Endpoints

1. **POST /ask** - Ask a question to the chatbot
    ```json
    {
        "text": "What was TCS's revenue in Q1?",
        "context_aware": true
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

#### Example API Usage

Using Python requests:

```python
import requests

# Ask a question
response = requests.post(
    "http://localhost:8000/ask",
    json={"text": "What was TCS revenue?", "context_aware": True}
)
print(response.json())

# Upload a PDF
with open('file.pdf', 'rb') as f:
    response = requests.post(
        "http://localhost:8000/upload-pdf",
        files={"file": f}
    )
print(response.json())

# Add ticker context
response = requests.post(
    "http://localhost:8000/add-ticker-context",
    json={"tickers": ["RELIANCE", "TCS"]}
)
print(response.json())
```

## Future Improvements

-   **Database Pruning:** Implement a mechanism to remove old or irrelevant databases.
-   **More sources:** Add more sources for DB population, like CSV, TXT, etc.
-   **UI/UX:** Improve overall user experience.
-   **Error Handling**: Improve overall error handling.
-   **API Enhancement:** Add more endpoints and features to the API.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

## License

This project is licensed under the [Your License] license.
