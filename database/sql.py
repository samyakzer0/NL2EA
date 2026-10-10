import datetime
import sqlparse

from sqlalchemy import create_engine, text
from services.llm import generate_content


def generate_sql_query(question, schema_text):
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
- For revenue by billing period, filter using invoices.billing_month.
- Use payments.payment_date only when asking when money was collected.
- Use invoices.amount for invoiced revenue.
- Use payments.amount for collected payment amounts.
- Invoice dates and payment dates do not necessarily represent
  the same reporting period.
- Use only actual table names and column names from the provided schema.
- Use the actual categorical values represented in the database.
  Do not assume the capitalization of status or category values.
- Do not filter out NULL prices when counting active subscriptions
  unless the question explicitly requires a price condition.
- When counting active paying customers by plan, use subscription
  status and customer counts; do not assume monthly_price must be non-NULL.
"""

    return  generate_content(prompt)


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

    statement_type = statement.get_type()

    if statement_type == "SELECT":
        return True

    if statement_type != "UNKNOWN":
        return False

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
        with engine.connect() as conn:

            with conn.begin():

                conn.execute(text("SET TRANSACTION READ ONLY"))

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