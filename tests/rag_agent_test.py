from agents.rag_agent import run_rag


question = "What is the refund period?"

answer = run_rag(question)

print(answer)