from dotenv import load_dotenv
load_dotenv(".env.local",override=True)


from app.graph import graph

result = graph.invoke({
    "message": "What was Zer0Labs' enterprise revenue in Q3 2026, and what does our enterprise SLA promise?"
})

print(result)
