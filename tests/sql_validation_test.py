from database.sql import validate_sql_query


queries = {
    "safe_select": "SELECT * FROM documents;",
    "safe_count": "SELECT COUNT(*) FROM documents;",
    "safe_cte": """
        WITH docs AS (
            SELECT * FROM documents
        )
        SELECT COUNT(*) FROM docs;
    """,
    "delete": "DELETE FROM documents;",
    "update": "UPDATE documents SET content = 'x';",
    "insert": "INSERT INTO documents(content) VALUES ('test');",
    "drop": "DROP TABLE documents;",
    "multiple": "SELECT * FROM documents; DELETE FROM documents;",
}


for name, query in queries.items():
    print(name, "=>", validate_sql_query(query))