from langchain_community.document_loaders import PyPDFLoader


def load_pdf(pdf_path):
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()
    return docs


def load_multiple_pdfs(pdf_paths):
    """Load and combine documents from multiple PDF file paths."""
    all_docs = []
    for path in pdf_paths:
        docs = load_pdf(path)
        # Tag each document with its source filename for traceability
        for doc in docs:
            doc.metadata["source_file"] = path
        all_docs.extend(docs)
    return all_docs