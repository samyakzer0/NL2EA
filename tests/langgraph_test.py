from app.graph import graph

result = graph.invoke({
    "message": "How many documents mention shipping?"
})

print(result)
