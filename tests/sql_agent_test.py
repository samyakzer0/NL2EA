from agents.sql_agent import run_sql
from database.schema import extract_database_schema, format_schema

from dotenv import load_dotenv
import os


load_dotenv()


schema = extract_database_schema(
    os.getenv("DATABASE_URL"),
    allowed_tables=["documents"]
)

schema_text = format_schema(schema)

question = "Delete all documents from the database"

result = run_sql(
    question,
    schema_text
)

print(result)