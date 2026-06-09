# 📚 MindFolio (AI PDF Assistant)

An intelligent, AI-powered PDF reader and analyzer that uses Retrieval-Augmented Generation (RAG) to help you instantly understand, interact with, and extract valuable study materials from your documents.

## ✨ Features

- **🧠 Intelligent Q&A (RAG):** Chat with your PDFs. The app uses ChromaDB and embeddings to accurately retrieve information and answer your questions alongside Mistral and Groq AI.
- **📝 Automated Study Materials:** Automatically generate comprehensive study notes and flashcards from your documents.
- **⚡ High Performance Processing:** Utilizes PyMuPDF for blazing-fast text extraction and concurrent API processing to quickly embed large documents without throttling.
- **📊 Report Generation:** Synthesize document information into structured PDF reports (powered by ReportLab).


## 🗂️ Project Structure

The project follows a clean, modular architecture:

- **`/ingestion`**: Handles the processing of documents (PDF loading, text splitting, embedding generation, and storing in the Chroma vector database).
- **`/retrieval`**: Manages the fetching of relevant context from the vector database based on user queries.
- **`/llm`**: Contains the core logic for the Large Language Model (prompts, model initialization, and RAG chains).

## 🛠️ Tech Stack

- **Language:** Python
- **AI Models:** Mistral API, Groq API
- **Vector Database:** ChromaDB
- **PDF Generation:** ReportLab


## 🚀 Getting Started

### Prerequisites

1. Python 3.8+
2. A Mistral API Key
3. A Groq API Key


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

## � Future Scope

- **📝 Advanced Notes Generation:** Detailed, structured study notes with customizable detail levels extracted directly from documents.
- **🗂️ Flashcard Export:** Generate and export flashcards seamlessly for integration with Anki or other spaced repetition software.
- **📊 Detailed PDF Reports:** Automatic synthesis of large documents into visually appealing, structured PDF reports and summaries (using ReportLab).


## �📄 License
MIT License
