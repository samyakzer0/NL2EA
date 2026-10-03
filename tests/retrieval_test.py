from retrieval.vector_store import create_retriever


retriever = create_retriever(k=3)

question = "What is the refund period?"

results = retriever.invoke(question)

for result in results:
    print(result.page_content)