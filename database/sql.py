import datetime
import sqlparse

from sqlalchemy import create_engine, text
from google import genai


def generate_sql_query(question, schema_text, client):
    prompt = f"""
You are an expert PostgreSQL SQL generator.

Database schema:
{schema_text}

User question:
{question}

Generate a SQL query that answers the user's question.

Rules:
- Return ONLY the SQL query.
- Use SELECT statements only.
- Do not use INSERT, UPDATE, DELETE, DROP, ALTER, or CREATE.
- Use only tables and columns present in the schema.
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
    )

    return response.text.strip()


def clean_sql_string(raw_sql):
    raw_sql = raw_sql.strip()

    if raw_sql.startswith("```"):
        lines = raw_sql.splitlines()

        lines = [
            line
            for line in lines
            if not line.strip().startswith("```")
        ]

        raw_sql = "\n".join(lines)

    return raw_sql.strip()


def validate_sql_query(sql_query):
    parsed = sqlparse.parse(sql_query)

    if not parsed:
        return False

    if len(parsed) != 1:
        return False

    statement = parsed[0]

    if statement.get_type() not in ("SELECT", "UNKNOWN"):
        return False

    if statement.get_type() == "UNKNOWN":
        first_token = statement.token_first(skip_cm=True)

        if first_token is None:
            return False

        if first_token.value.upper() != "WITH":
            return False

    return True


def serialize_row_value(val):

    if isinstance(val, (datetime.date, datetime.datetime)):
        return val.isoformat()

    if isinstance(val, bytes):
        return val.decode("utf-8", errors="replace")

    if hasattr(val, "__str__") and type(val).__name__ == "Decimal":
        return float(val)

    return val


def execute_sql(db_url, query):

    engine = create_engine(db_url)

    try:
        with engine.begin() as conn:

            result = conn.execute(text(query))

            rows = [
                {
                    k: serialize_row_value(v)
                    for k, v in dict(row._mapping).items()
                }
                for row in result
            ]

            return rows

    except Exception as e:

        print(f"Error executing SQL: {e}")

        return []

    finally:
        engine.dispose()