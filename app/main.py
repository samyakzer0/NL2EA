from fastapi import FastAPI
from pydantic import BaseModel

from app.graph import graph


app = FastAPI(
    title="EAQL",
    description="Enterprise Aware RAG & Query Platform",
    version="1.0.0"
)


class QueryRequest(BaseModel):
    question: str


@app.get("/")
def root():
    return {
        "message": "EAQL API is running"
    }


@app.post("/query")
def query(request: QueryRequest):

    result = graph.invoke({
        "message": request.question
    })

    return {
        "answer": result["result"]
    }