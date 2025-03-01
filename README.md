# Finance Chatbot - Powered by Gemini and LangChain

This project is a financial advisor chatbot that leverages the power of Google's Gemini model (specifically `gemini-1.5-pro`) and the LangChain framework to provide users with insights and information based on uploaded financial documents. It can answer questions, extract financial data, and structure responses in JSON format for easy processing.

## Features

*   **Context-Aware Responses:** The chatbot analyzes uploaded PDF documents to understand the context and provide relevant answers to user questions.
*   **Financial Data Extraction:** It can extract and present financial information, including stock details, YoY growth, revenue by segment, and more.
*   **Streamlit Interface:** A user-friendly web interface built with Streamlit allows users to interact with the chatbot.
*   **Gemini Model:** Utilizes the advanced capabilities of the `gemini-1.5-pro` model for natural language understanding and generation.
* **Langchain Integration**: The project extensively leverages LangChain's capabilities for building chains, and managing prompts.
* **PDF Handling:** The project can load and split PDF files into smaller chunks to facilitate the processing.

## Technologies Used

*   **LangChain:** A framework for building applications with large language models.
*   **Google Gemini API:**  For the core natural language processing and generation.
*   **Streamlit:** For creating the interactive web interface.
*   **PyPDF:** For PDF file loading and processing.
*   **RecursiveCharacterTextSplitter**: to split large text documents into chunks
*   **python-dotenv:** For managing environment variables.
* **llama-index**: for potential future upgrades.

## Prerequisites

*   **Python 3.8+**
*   **Google Gemini API Key:**  You need a valid Google Gemini API key.
*   **LangChain API Key:** You will need a LangChain API key for tracing and monitoring.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/saxena-udit/learning-ai.git
    cd learning-ai/chatbot
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Linux/macOS
    venv\Scripts\activate  # On Windows
    ```

3.  **Install the required packages:**
    ```bash
    pip install -r ../requirements.txt
    ```

4.  **Set up environment variables:**

    *   Create a `.env` file in the `learning-ai` directory (one level up from the chatbot directory) and add your API keys:

    ```properties
    GEMINI_API_KEY=YOUR_GEMINI_API_KEY
    LANGCHAIN_API_KEY=YOUR_LANGCHAIN_API_KEY
    LANGCHAIN_PROJECT=Finance Chatbot
    ```

    *   Replace `YOUR_GEMINI_API_KEY` and `YOUR_LANGCHAIN_API_KEY` with your actual API keys.

## How to Use

1.  **Run the Streamlit app:**
    ```bash
    streamlit run app.py
    ```

2.  **Interact with the Chatbot:**

    *   Open your web browser and go to the URL provided by Streamlit (usually `http://localhost:8501`).
    *   **Upload a PDF:** In the left sidebar, you can upload a financial document (PDF) that you want the chatbot to use as context.
    *   **Ask a Question:** In the main area, type your question in the text input field.
    *   **View the Response:** The chatbot will generate a response, either in plain text or as a structured JSON table, depending on the question and context.
    *   **No PDF:** If you do not provide a PDF, the chatbot will still try to provide you with information.

## Code Structure

*   **`app.py`:** The main Streamlit application file, handles the UI, file uploads, and interaction with the LangChain.
*   **`langchain_gemini.py`:** Contains the core logic for interacting with the Gemini model, defining prompts, creating the retrieval chain, loading and splitting pdf files.
* **`requirements.txt`**: List of all dependencies

## Key Code Details

*   **`load_and_split_pdf(uploaded_file)`:** Loads a PDF, splits it into chunks, and returns the chunks.
*   **`create_prompt_template(has_context)`:** Dynamically creates a prompt template based on whether context is available.
*   **`retrieval_chain(prompt, retriever, uploaded_file)`:** Creates the LangChain chain for retrieving and responding to user queries.
* **`ChatGoogleGenerativeAI`**: used as a wrapper for calling Gemini.

## Future Enhancements

*   **Web Data Retrieval:** Enhance the chatbot to gather information from live web sources (e.g., stock market APIs) in addition to uploaded files.
*   **Improved Error Handling:** Implement more robust error handling and logging for better debugging and user experience.
* **More Langchain features**: integrate more langchain features like, agents and tools.
*   **UI/UX improvements:** Add some UI/UX features, like keeping the conversation context.
*   **More models:** Add the option to choose between more LLMs.

## Contributing

Contributions are welcome! If you'd like to improve the project, feel free to fork the repository and submit a pull request.

## License

[Specify the license for your project here, e.g., MIT License]
