import os
import shutil
from langchain_community.vectorstores import Chroma

def create_vectorstore(chunks, embedding_model):
    persist_dir = "./chroma_db"
    
    # Delete the old database so we always start fresh
    if os.path.exists(persist_dir):
        shutil.rmtree(persist_dir)
        
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_model,
        persist_directory=persist_dir
    )

    return vectorstore