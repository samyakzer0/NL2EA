from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from google import genai
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_postgres import PGVector
from tests.gemini_embedding_test import GeminiEmbedding
from database.schema import extract_database_schema, format_schema
from database.sql import (
    generate_sql_query,
    clean_sql_string,
    validate_sql_query,
    execute_sql
)
from dotenv import load_dotenv
from sqlalchemy import create_engine, text,inspect
import datetime
import sqlparse
import os



load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class State(TypedDict):
    message: str
    route: str
    result: str

builder = StateGraph(State)


vector_store = PGVector(
    embeddings=GeminiEmbedding(),
    collection_name="nl2ea_docs_v2",
    connection=os.getenv("DATABASE_URL"),
    use_jsonb=True
)

retriever = vector_store.as_retriever(search_kwargs={"k": 3})

llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", api_key=os.getenv("GEMINI_API_KEY"), temperature=0.2)

prompt = ChatPromptTemplate.from_template("""
You are an AI assistant that answers questions using only the provided context.

Context: {context}

Question: {question}

If the answer is unavailable in the context, say "I don't know".

Answer:"""
)

rag_chain = ({"context":retriever, "question":RunnablePassthrough()} | prompt | llm )


schema = extract_database_schema(os.getenv("DATABASE_URL"),allowed_tables=["documents"])
schema_text=format_schema(schema)
print(schema_text)



#sql node
def sql(state: State):
    question = state['message']
    query = generate_sql_query(
    question,
    schema_text,
    client
    )

    print(f"Generated SQL Query: {query}")

    if not validate_sql_query(query):
        return {
            "result": "Unsafe SQL query generated."
        }
    rows = execute_sql(os.getenv("DATABASE_URL"), query)
    return {
        "result": str(rows)
    }


#rag node
def rag(state: State):
      response = rag_chain.invoke(state['message'])
      return {
            "result" : response.content[0]["text"]
      }



def classify(question):
     prompt = f"""
      Classify the following question into exactly one category:

    - rag: questions that require information from documents
    - sql: questions that require querying structured database data

    Question: {question}

    Return only:
    rag
    or
    sql"""

     response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
     )
     return response.text.strip()


def answer(state:State):
    question = state['message']
    result = state['result']
    prompt = f"""

    You are an AI analytics assistant.

User question:
{question}

Retrieved result:
{result}

Answer the user's question clearly and concisely using the retrieved result.

Do not mention internal routing, SQL, RAG, embeddings, or implementation details.

If the result does not contain enough information, say so clearly.
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
    )

    return {
        "result": response.text.strip()
    }






def router(state: State):
     return classify(state['message'])


builder.add_node("rag", rag)
builder.add_node("sql", sql)

builder.add_conditional_edges(START, router, {
    "rag": "rag",
    "sql": "sql"
})
builder.add_node("answer", answer)
builder.add_edge("rag", "answer")
builder.add_edge("sql", "answer")
builder.add_edge("answer", END)

graph = builder.compile()

result = graph.invoke({
    "message": "Delete all documents from the database"
})

print(result)
