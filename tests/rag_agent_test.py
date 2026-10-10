from dotenv import load_dotenv
load_dotenv(".env.local", override=True)

from retrieval.vector_store import create_retriever
from langchain_google_genai import ChatGoogleGenerativeAI

retriever = create_retriever(k=3)

question = "What was Zer0Labs' enterprise revenue in Q3 2026?"

docs = retriever.invoke(question)

context = "\n\n".join(
    doc.page_content for doc in docs
)

llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    temperature=0
)

prompt = f"""
Answer the question using only the context below.
If the answer is not available, say so.
Do not invent financial figures.

Context:
{context}

Question: {question}
"""

response = llm.invoke(prompt)

print("Question:", question)
for block in response.content:
    if isinstance(block, dict) and block.get("type") == "text":
        print(block["text"])