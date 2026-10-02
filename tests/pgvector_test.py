from langchain_postgres import PGVector
from gemini_embedding_test import GeminiEmbedding
import os
from langchain_core.runnables import RunnablePassthrough
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
load_dotenv()

llm=ChatGoogleGenerativeAI(model="gemini-flash-latest", api_key=os.getenv("GEMINI_API_KEY"), temperature=0.2)
prompt = ChatPromptTemplate.from_template("""
You are an AI assistant that answers questions using only the provided context.
Context: {context}
Question: {question}

If the answer is unavailable in the context, say "I don't know".
Answer:""")
# chain = prompt | llm
connection = os.getenv("DATABASE_URL")
embeddings = GeminiEmbedding()
vector_store = PGVector(
    embeddings=embeddings,
    collection_name="nl2ea_docs_v2",
    connection=connection,
    use_jsonb=True
)
retriever = vector_store.as_retriever(search_kwargs={"k": 3})
rag_chain = ({"context":retriever, "question":RunnablePassthrough()} | prompt | llm )
question = "How long can I get a refund?"
# results = retriever.invoke(question)
# context = "\n".join([result.page_content for result in results])
documents = [
    "The refund period is 30 days.",
    "Standard shipping takes 5 to 7 business days.",
    "Customers can cancel an order within 24 hours.",
    "Premium customers receive free shipping.",
    "Refunds are processed within 5 business days after approval.",
    "The company operates customer support from 9 AM to 6 PM.",
    "Password resets can be requested from the account settings page.",
    "International shipping is currently unavailable."
]

response = rag_chain.invoke(question)

print (response.content[0]["text"])

# ids=vector_store.add_texts(documents)
# response = chain.invoke({"context": context, "question": question})
# print(response.content[0]["text"])
