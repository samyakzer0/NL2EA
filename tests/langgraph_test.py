from typing import TypedDict
from langgraph.graph import StateGraph, START
from google import genai
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_postgres import PGVector
from gemini_embedding_test import GeminiEmbedding
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


#db functions
def extract_database_schema(db_url):
     engine = create_engine(db_url)
     inspector = inspect(engine)
     schema = {}

     for table_name in inspector.get_table_names():
          columns = inspector.get_columns(table_name)
          schema[table_name]=[]
          for column in columns:
             schema[table_name].append({
               "name": column["name"],
               "type": str(column["type"])
          })
     engine.dispose()          
     return schema

def format_schema(schema):
     formatted=[]

     for table,columns in schema.items():
          formatted.append(f"Table: {table}")
          for column in columns:
               formatted.append(f"  Column: {column['name']} - Type: {column['type']}")
     return "\n".join(formatted)

schema = extract_database_schema(os.getenv("DATABASE_URL"))
schema_text=format_schema(schema)
print(schema_text)



#sql generator
def generate_sql_query(question, schema_text):
    prompt = f"""
You are an expert postgreSQL SQL generator.

Database schema:
{schema_text}

User question:
{question}

Generate a SQL query that answers the user's question.

Rules:
- Return ONLY the SQL query.
- Use SELECT statements only.
- Do not use INSERT, UPDATE, DELETE, DROP, ALTER, or CREATE.
- Use only tables and columns present in the schema.
"""
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
    )
    return response.text.strip()

#sql cleaner
def clean_sql_string(raw_sql):
    raw_sql = raw_sql.strip()

    if raw_sql.startswith("```"):
        lines = raw_sql.splitlines()

        # Remove ```sql / ```
        lines = [
            line for line in lines
            if not line.strip().startswith("```")
        ]

        raw_sql = "\n".join(lines)

    return raw_sql.strip()

#sql validator

def validate_sql_query(sql_query):
    parsed = sqlparse.parse(sql_query)

    if not parsed:
        return False

    if len(parsed) != 1:
        return False

    statement = parsed[0]

    if statement.get_type() not in ("SELECT", "UNKNOWN"):
        return False

    if statement.get_type() == "UNKNOWN":
        first_token = statement.token_first(skip_cm=True)

        if first_token is None:
            return False

        if first_token.value.upper() != "WITH":
            return False

    return True

#sql serializer and executor

def serialize_row_value(val):
    if isinstance(val, (datetime.date, datetime.datetime)):
        return val.isoformat()
    if isinstance(val, bytes):
        return val.decode("utf-8", errors="replace")
    if hasattr(val, "__str__") and type(val).__name__ == "Decimal":
        return float(val)
    return val

def execute_sql(db_url, query):
     engine = create_engine(db_url)

     try:
          with engine.begin() as conn:
               result = conn.execute(text(query))
               rows = [{k:serialize_row_value(v) for k,v in dict(row._mapping).items()} for row in result]
               return rows
     except Exception as e:
          print(f"Error executing SQL: {e}")
          return []
     finally:
          engine.dispose()

#sql node
def sql(state: State):
    question = state['message']
    query = generate_sql_query(question, schema_text)

    query = clean_sql_string(query)

    print(f"Generated SQL Query: {query}")

    if not validate_sql_query(query):
        return {
            "message": "Unsafe SQL query generated."
        }
    rows = execute_sql(os.getenv("DATABASE_URL"), query)
    return {
        "message": f"SQL Query Result: {rows}"
    }


#rag node
def rag(state: State):
      response = rag_chain.invoke(state['message'])
      return {
            "message" : response.content[0]["text"]
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


def router(state: State):
     return classify(state['message'])


builder.add_node("rag", rag)
builder.add_node("sql", sql)
builder.add_conditional_edges(START, router, {
    "rag": "rag",
    "sql": "sql"
})

graph = builder.compile()

result = graph.invoke({
    "message": "What is our refund policy?"
})

print(result)