import os
from typing import TypedDict

from dotenv import load_dotenv
from google import genai
from langgraph.graph import StateGraph, START, END

from agents.rag_agent import run_rag
from agents.sql_agent import run_sql

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

class State(TypedDict):
    message: str
    result: str

builder = StateGraph(State)

#sql node
def sql(state: State):
    question = state["message"]

    result = run_sql(question)

    return {
        "result": result
    }

#rag node
def rag(state: State):
    question = state['message']
    result = run_rag(question)
    return {
        "result": result
    }


def classify(question):
     prompt = f"""
     You are a routing classifier for an enterprise analytics system.

Classify the user's question into exactly ONE category:

SQL:
- Counting records
- Filtering records
- Aggregations such as COUNT, SUM, AVG, MIN, MAX
- Sorting or grouping structured data
- Questions asking for database records or values
- Questions containing phrases like:
  "how many", "count", "list", "show me", "which records", "how much"

RAG:
- Questions asking for information, explanations, or facts contained
  in unstructured documents
- Questions requiring semantic document retrieval
- Questions such as:
  "What is the refund period?"
  "What does the refund policy say?"
  "What is the company's shipping policy?"

IMPORTANT:
The word "document" alone does NOT mean RAG.

For example:
"How many documents mention shipping?"
=> sql

"Show me documents that mention refunds"
=> sql

"What is the refund period?"
=> rag

"Who is the CEO of the company?"
=> rag

User question:
{question}

Return ONLY one word:
sql
or
rag
"""

     response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
     )
     return response.text.strip()

def answer(state: State):

    question = state["message"]
    result = state["result"]

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

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt,
        )

        

        return {
            "result": response.text.strip()
        }

    except Exception as e:
        print("\nANSWER ERROR:")
        print(type(e).__name__, e)

        return {
            "result": "Answer generation failed."
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