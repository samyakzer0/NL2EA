from database.schema import extract_database_schema, format_schema
from dotenv import load_dotenv
import os

load_dotenv()

schema = extract_database_schema(
    os.getenv("DATABASE_URL")
)

print(format_schema(schema))