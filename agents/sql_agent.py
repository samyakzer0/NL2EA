import os

from dotenv import load_dotenv


from database.schema import extract_database_schema, format_schema

from database.sql import (
    generate_sql_query,
    clean_sql_string,
    validate_sql_query,
    execute_sql
)

load_dotenv()

def run_sql(question):

    schema = extract_database_schema(
        os.getenv("DATABASE_URL"),
        allowed_tables=["documents"]
    )

    schema_text = format_schema(schema)

    query = generate_sql_query(
    question,
    schema_text
    )

    query = clean_sql_string(query)

    if not validate_sql_query(query):
        return "Unsafe SQL query generated."

    rows = execute_sql(
        os.getenv("DATABASE_URL"),
        query
    )

    return str(rows)