from dotenv import load_dotenv
load_dotenv(".env.local",override=True)


from app.graph import graph

result = graph.invoke({
    "message": "How many documents mention shipping?"
})

print(result)
