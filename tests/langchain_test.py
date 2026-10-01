from langchain_core.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv
load_dotenv()
from langchain_google_genai import  ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", api_key=os.getenv("GEMINI_API_KEY"), temperature=0.2)

prompt = ChatPromptTemplate.from_template("""
You are an AI assistant that answers questions using only the provided context.

Context:
{context}

Question:
{question}

If the answer is unavailable in the context, say "I don't know".

""")

chain = prompt | llm
response = chain.invoke({"context": "The refund period is 30 days.", "question": "What is the refund period?"})
print(response.content)