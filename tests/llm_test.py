from services.llm import generate_content


response = generate_content(
    "Reply with exactly: EAQL LLM service works"
)

print(response)