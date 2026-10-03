import os

from dotenv import load_dotenv
from google import genai

from database.sql import (
    generate_sql_query,
    clean_sql_string,
    validate_sql_query,
    execute_sql
)


load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

def run_sql(question, schema_text):
    query = generate_sql_query(
        question,
        schema_text,
        client
    )

    query = clean_sql_string(query)

    if not validate_sql_query(query):
        return "Unsafe SQL query generated."

    rows = execute_sql(
        os.getenv("DATABASE_URL"),
        query
    )

    return str(rows)