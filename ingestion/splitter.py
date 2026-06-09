from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_documents(docs):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )

    chunks = splitter.split_documents(docs)

    return chunks