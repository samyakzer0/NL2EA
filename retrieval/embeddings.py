import os

from dotenv import load_dotenv
from google import genai


load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


class GeminiEmbedding:

    def embed_documents(self, documents):

        results = client.models.embed_content(
            model="gemini-embedding-001",
            contents=documents
        )

        return [
            embedding.values
            for embedding in results.embeddings
        ]

    def embed_query(self, query):

        result = client.models.embed_content(
            model="gemini-embedding-001",
            contents=[query]
        )

        return result.embeddings[0].values