import os

from dotenv import load_dotenv
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from retrieval.vector_store import create_retriever


load_dotenv(".env.local", override=True)


def create_rag_chain():

    retriever = create_retriever(k=3)

    llm = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite",
        api_key=os.getenv("GEMINI_API_KEY")
    )

    prompt = ChatPromptTemplate.from_template("""
You are an AI assistant that answers questions using only the provided context.

Context:
{context}

Question:
{question}

If the answer is unavailable in the context, say "I don't know".

Answer:
""")

    rag_chain = (
        {
            "context": retriever,
            "question": RunnablePassthrough()
        }
        | prompt
        | llm
    )

    return rag_chain


def run_rag(question):

    rag_chain = create_rag_chain()

    response = rag_chain.invoke(question)

    return response.content[0]["text"]