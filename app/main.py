from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.graph import graph


app = FastAPI(
    title="EAQL",
    description="Enterprise Aware RAG & Query Platform",
    version="1.0.0"
)


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    answer: str


@app.get("/")
def root():
    return {
        "message": "EAQL API is running"
    }

@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):

    if not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    try:
        result = graph.invoke({
            "message": request.question
        })

        return QueryResponse(
            answer=result["result"]
        )

    except Exception as e:
        print(f"Query error: {e}")

        raise HTTPException(
            status_code=500,
            detail="Failed to process the query."
        )