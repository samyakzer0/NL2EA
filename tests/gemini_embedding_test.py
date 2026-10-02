from google import genai
import os
from dotenv import load_dotenv
load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class GeminiEmbedding:
    def embed_documents(self, documents):
        results =client.models.embed_content(
            model="gemini-embedding-001",
            contents=documents
        )

        return [embedding.values for embedding in results.embeddings]
    

    def embed_query(self, query):
        result = client.models.embed_content(
            model="gemini-embedding-001",
            contents=[query]
        )

        return result.embeddings[0].values

embedding = GeminiEmbedding()
doc = embedding.embed_documents(documents = [
    "The refund period is 30 days.",
    "Standard shipping takes 5 to 7 business days."
])

query = embedding.embed_query(query = "How long can I get a refund?")


