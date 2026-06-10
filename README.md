# 📚 MindFolio (AI PDF Assistant)

**MindFolio** is an intelligent, AI-powered document analysis and learning assistant. Built with Python and Streamlit, it leverages advanced **Retrieval-Augmented Generation (RAG)** to transform static PDF documents into interactive learning experiences. Users can upload multiple PDFs, chat with their documents, and automatically generate comprehensive study materials including structured notes, multiple-choice quizzes, and interactive flashcards.

## ✨ Features

- **🧠 Intelligent Q&A (RAG):** Chat with your PDFs. The app uses ChromaDB, advanced semantic search (with Query Expansion and MMR), and a multi-model architecture routing tasks between Mistral and Groq AI.
- **📝 Automated Study Materials:** Automatically generate comprehensive study notes, practice quizzes, and interactive flashcards from your documents, exported as highly styled PDFs via ReportLab.
- **🛡️ Hallucination Prevention:** Includes a dedicated Verifier Layer to fact-check answers. If the system cannot answer from the documents, it dynamically falls back to an Internet Search.
- **⚡ High Performance Processing:** Utilizes PyMuPDF for blazing-fast text extraction and concurrent API processing for rapid document embedding and searching.
- **🎨 Modern UI:** A customized, glassmorphic Streamlit interface with dark mode, tabbed navigation, and animated processing states.

## 🗂️ Project Structure

The project follows a clean, modular architecture:

- **`app.py`**: The main entry point containing the Streamlit UI, session state management, file uploading logic, and orchestration of workflows.
- **`/ingestion`**: Handles document extraction (`PyMuPDFLoader`), text splitting (`RecursiveCharacterTextSplitter`), embedding generation (`mistral-embed` via threading), and vector storage (in-memory `ChromaDB`).
- **`/retrieval`**: Manages the fetching of relevant context with expanded semantic search, concurrent search variations, and deduplication.
- **`/llm`**: Contains the AI router, prompting logic, fallback mechanisms, and the hallucination Verifier Layer.
- **`/generation`**: Contains scripts to query LLMs for specific outputs (notes, quizzes, flashcards) and dynamically construct styled PDF documents using `ReportLab`.

## 🛠️ Tech Stack

- **Language:** Python 3.8+
- **Frontend / UI:** Streamlit (with custom CSS)
- **Document Processing:** `PyMuPDF` & `LangChain`
- **Vector Database:** ChromaDB (In-memory)
- **Embeddings:** Mistral API (`mistral-embed`)
- **LLM Providers:** 
  - **Mistral API** (`ministral-8b-2512`, `open-mistral-nemo`) for creative and structured content generation.
  - **Groq API** (`llama-3.1-8b`, `llama-3.3-70b`, `llama-4-scout-17b`, `groq/compound`) for fast query rewriting, factual Q&A, and internet search.
- **PDF Generation:** `ReportLab`

## 🚀 Getting Started

### Prerequisites

1. Python 3.8+
2. A [Mistral API Key](https://console.mistral.ai/)
3. A [Groq API Key](https://console.groq.com/)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd MindFolio
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Environment Variables:**
   Create a `.env` file in the root directory and add your API keys:
   ```env
   MISTRAL_API_KEY=your_mistral_api_key_here
   GROQ_API_KEY=your_groq_api_key_here
   ```

### Running the App

To start the main application:
```bash
streamlit run app.py
```

## 🔮 Future Scope

- Granular control over the complexity level of generated notes.
- Direct export integrations for spaced-repetition software (like Anki) for flashcards.
- Enhanced layout controls for ReportLab generation, including inserting charts or tables extracted from the original PDFs.

## 📄 License

MIT License
