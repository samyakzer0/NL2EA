from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy import create_engine, text
from google import genai

engine = create_engine(os.getenv("DATABASE_URL"))
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", api_key=os.getenv("GEMINI_API_KEY"), temperature=0.2)

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

prompt = ChatPromptTemplate.from_template("""
You are an AI assistant that answers questions using only the provided context.

Context:
{context}

Question:
{question}

If the answer is unavailable in the context, say "I don't know".


""")

chain = prompt | llm
question = "When can I cancel my order?"
results=retrieve(question,top_k=3)
context = "\n".join ([row.content for row in results])
response = chain.invoke({"context": context, "question": question})
print(response.content)
