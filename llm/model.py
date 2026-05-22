from langchain_google_genai import ChatGoogleGenerativeAI

def load_llm():

    model = ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite",
        temperature=0.5,
    )

    return model