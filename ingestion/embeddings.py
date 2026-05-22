from langchain_huggingface import HuggingFaceEmbeddings


def load_embedding_model():
    embedding_model = HuggingFaceEmbeddings(
        model_name="BAAI/bge-small-en"
    )

    return embedding_model