import os

from dotenv import load_dotenv
from google import genai
from sqlalchemy import create_engine, text

load_dotenv()

database_url = os.getenv("DATABASE_URL")
gemini_api_key = os.getenv("GEMINI_API_KEY")

engine = create_engine(database_url)
client = genai.Client(api_key=gemini_api_key)

# query = "What is the refund period?"
# result = client.models.embed_content(
#     model="gemini-embedding-001",
#     contents=[query]
# )
# embedding = result.embeddings[0].values

# with engine.begin() as conn:
#     result = conn.execute(text("""
#         SELECT id,content,embedding <=> :embedding AS similarity
#         FROM documents
#         ORDER BY similarity ASC
#         LIMIT 5
#     """), {
#         "embedding": f"[{','.join(map(str, embedding))}]"
#     })

#     for row in result:
#         print(row)



def retrieve(query,top_k=3):
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=[query]
    )
    embedding = result.embeddings[0].values

    with engine.begin() as conn:
        result = conn.execute(text("""
            SELECT id,content,embedding <=> :embedding AS similarity
            FROM documents
            ORDER BY similarity ASC
            LIMIT :top_k
        """), {
            "embedding": f"[{','.join(map(str, embedding))}]",
            "top_k": top_k
        })

        return [row for row in result]

def answer(query):
    results=retrieve(query,top_k=3)
    context="\n".join([row.content for row in results])

    prompt = f"""

    Context: {context}
    Question: {query}

    You are a helpful assistant. Use the following context to answer the question below. If the context does not contain enough information, say "I don't know".

    """

    return client.models.generate_content(
        model="gemini-2.5-flash",
        ContentDispositionHeader=prompt,
    )

answer = answer("What is the refund period?")
print(answer)
