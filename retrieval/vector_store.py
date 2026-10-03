import os

from dotenv import load_dotenv
from langchain_postgres import PGVector

from retrieval.embeddings import GeminiEmbedding


load_dotenv()


def create_vector_store():

    return PGVector(
        embeddings=GeminiEmbedding(),
        collection_name="nl2ea_docs_v2",
        connection=os.getenv("DATABASE_URL"),
        use_jsonb=True
    )


def create_retriever(k=3):

    vector_store = create_vector_store()

    return vector_store.as_retriever(
        search_kwargs={"k": k}
    )