import os

from dotenv import load_dotenv
from google import genai
from sqlalchemy import create_engine,text

load_dotenv()

database_url = os.getenv("DATABASE_URL")
gemini_api_key = os.getenv("GEMINI_API_KEY")

engine = create_engine(database_url)
client = genai.Client(api_key=gemini_api_key)
document_text = ["The refund period is 30 days.",

"Standard shipping takes 5 to 7 business days.",

"Customers can cancel an order within 24 hours.",

"Premium customers receive free shipping.",

"Refunds are processed within 5 business days after approval.",

"The company operates customer support from 9 AM to 6 PM.",

"Password resets can be requested from the account settings page.",

"International shipping is currently unavailable."]

result = client.models.embed_content(
    model="gemini-embedding-001",
    contents=document_text
)

with engine.begin() as conn:

    for document, embedding_result in zip(
        document_text,
        result.embeddings
    ):

        embedding = embedding_result.values

        conn.execute(
            text("""
                INSERT INTO documents (content, embedding)
                VALUES (:content, :embedding)
            """),
            {
                "content": document,
                "embedding": f"[{','.join(map(str, embedding))}]"
            }
        )


    print("Documents inserted with embedding vectors.")