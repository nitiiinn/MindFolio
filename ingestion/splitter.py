from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_documents(docs):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=2500,
        chunk_overlap=400,
    )

    chunks = splitter.split_documents(docs)

    return chunks