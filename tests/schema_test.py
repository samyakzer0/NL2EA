from dotenv import load_dotenv
import os

load_dotenv(".env.local", override=True)

from database.schema import extract_database_schema, format_schema

schema = extract_database_schema(
    os.getenv("DATABASE_URL"),
    allowed_tables=[
        "customers",
        "plans",
        "subscriptions",
        "invoices",
        "payments",
        "usage",
        "employees"
    ],
    schema_name="zer0labs"
)

print(format_schema(schema))