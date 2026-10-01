from langchain_postgres import PGVector
from gemini_embedding_test import GeminiEmbedding
import os
from dotenv import load_dotenv
load_dotenv()

connection = os.getenv("DATABASE_URL")
embeddings = GeminiEmbedding()
vector_store = PGVector(
    embeddings=embeddings,
    collection_name="nl2ea_docs",
    

)