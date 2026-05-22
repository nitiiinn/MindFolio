from langchain_core.output_parsers import StrOutputParser


def create_chain(prompt, model):

    parser = StrOutputParser()

    chain = prompt | model | parser

    return chain