from typing import TypedDict
from dotenv import load_dotenv

from langgraph.graph import StateGraph, START, END
from services.llm import generate_content
from agents.rag_agent import run_rag
from agents.sql_agent import run_sql

load_dotenv()


class State(TypedDict):
    message: str
    result: str
    sql_result: str
    rag_result: str

builder = StateGraph(State)

#sql node
def sql(state: State):
    question = state["message"]

    result = run_sql(question)

    return {
        "result": result,
        "sql_result": result
    }

#rag node
def rag(state: State):
    question = state['message']
    result = run_rag(question)
    return {
        "result": result,
        "rag_result": result
    }


def classify(question):
     prompt = f"""
You are a routing classifier for an enterprise analytics system.

Classify the question into exactly ONE category:

sql:
Requires structured database records, counts, filtering,
aggregations, sorting, or grouping.

rag:
Requires information from company documents, policies,
contracts, explanations, or documentation.

hybrid:
Requires BOTH structured database information AND
information from company documents.

Examples:
"How many active subscriptions do we have?" -> sql
"What does our enterprise SLA promise?" -> rag
"What was Q3 enterprise revenue, and what does our SLA promise?" -> hybrid

The word "document" alone does not imply rag.

User question:
{question}

Return ONLY one word: sql, rag, or hybrid.
"""

     category = generate_content(prompt).strip().lower()

     if "hybrid" in category:
         return "hybrid"
     if "sql" in category:
         return "sql"
     if "rag" in category:
         return "rag"

     return "rag"  # default to rag if classification is unclear


def hybrid(state: State):
    question = state["message"]

    prompt = f"""
You are a question decomposition assistant.

Split the user's question into two focused questions:

1. sql_question: Only the structured database information needed.
2. rag_question: Only the information needed from company documents.

Rules:
- Preserve the user's requested dates, filters, and entities.
- SQL questions must ask for database facts or calculations.
- RAG questions must ask about policies, contracts, SLAs,
  product documentation, or other company knowledge.
- Do not answer the questions.
- Return valid JSON with exactly these keys:
  sql_question and rag_question.

If a category is not needed, set its value to an empty string.

User question:
{question}
"""

    import json

    try:
        decomposition = generate_content(prompt)

        if isinstance(decomposition, list):
            decomposition = "".join(
                item.get("text", "")
                for item in decomposition
                if isinstance(item, dict)
            )

        decomposition = str(decomposition).strip()
        decomposition = decomposition.removeprefix("```json").removesuffix("```").strip()

        questions = json.loads(decomposition)

        sql_question = questions.get("sql_question", "").strip()
        rag_question = questions.get("rag_question", "").strip()

    except Exception as e:
        print("QUESTION DECOMPOSITION ERROR:", e)
        return {
            "result": "I couldn't safely separate the database and document questions."
        }

    sql_result = (
        run_sql(sql_question)
        if sql_question
        else "Not required for this question."
    )

    rag_result = (
        run_rag(rag_question)
        if rag_question
        else "Not required for this question."
    )

    print("SQL QUESTION:", sql_question)
    print("RAG QUESTION:", rag_question)

    return {
        "sql_result": str(sql_result),
        "rag_result": str(rag_result),
        "result": (
            f"STRUCTURED DATABASE RESULT:\n{sql_result}\n\n"
            f"DOCUMENT RETRIEVAL RESULT:\n{rag_result}"
        )
    }


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
        return {"result": generate_content(prompt)}

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
builder.add_node("hybrid", hybrid)
builder.add_conditional_edges(START, router, {
    "rag": "rag",
    "sql": "sql",
    "hybrid": "hybrid"
})
builder.add_node("answer", answer)
builder.add_edge("rag", "answer")
builder.add_edge("sql", "answer")
builder.add_edge("hybrid", "answer")
builder.add_edge("answer", END)

graph = builder.compile()