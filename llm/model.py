from langchain_groq import ChatGroq


def load_llm():

    model = ChatGroq(
        model_name="llama-3.1-8b-instant",
        temperature=0.5,
    )

    return model