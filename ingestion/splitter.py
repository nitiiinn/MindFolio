from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_documents(docs):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=330,
        chunk_overlap=30,
    )

    chunks = splitter.split_documents(docs)

    return chunks