from dotenv import load_dotenv
load_dotenv(".env.local", override=True)

from retrieval.vector_store import create_retriever

retriever = create_retriever(k=3)

question = "What was Zer0Labs' enterprise revenue in Q3 2026?"
results = retriever.invoke(question)

for i, doc in enumerate(results, 1):
    print(f"\n--- Result {i} ---")
    print("Source:", doc.metadata.get("source"))
    print(doc.page_content[:500])