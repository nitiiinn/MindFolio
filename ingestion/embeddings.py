from langchain_huggingface import HuggingFaceEmbeddings

def load_embedding_model():
    """Loads the heavy-duty BAAI/bge-large-en-v1.5 embedding model onto the GPU."""
    
    embedding_model = HuggingFaceEmbeddings(
        model_name="BAAI/bge-large-en-v1.5", # The highest accuracy model
        model_kwargs={'device': 'cuda'},     # Pushes the workload to your RTX 4050
        encode_kwargs={'normalize_embeddings': True} # Crucial for accurate retrieval
    )
    
    return embedding_model