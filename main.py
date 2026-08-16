import re
import datetime
from typing import Any, Dict, List
import sqlparse
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from sqlalchemy import create_engine, inspect, text
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="NL2SQL Engine",
    description="A lightweight Natural Language to SQL Backend-as-a-Service powered by LLM's and SQLAlchemy.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    db_connection_uri: str = Field(
        ...,
        description="SQLAlchemy database connection URI (e.g. mysql+pymysql://user:pass@host:3306/db, sqlite:///test.db)"
    )
    user_prompt: str = Field(
        ...,
        description="Natural language question to translate into SQL and execute"
    )
    gemini_api_key: str = Field(
        ...,
        description="Google Gemini or any other LLM API key"
    )


class QueryResponse(BaseModel):
    status: str
    sql_query: str
    row_count: int
    data: List[Dict[str, Any]]


def extract_database_schema(db_uri: str) -> str:
    """
    Connects to the specified database URI and extracts table names
    and column definitions.
    """
    engine = create_engine(db_uri)
    try:
        inspector = inspect(engine)

        schema_text = ""
        for table_name in inspector.get_table_names():
            schema_text += f"\nTable: {table_name}\nColumns:\n"
            for column in inspector.get_columns(table_name):
                schema_text += f"  - {column['name']} ({column['type']})\n"

        return schema_text
    except Exception as e:
        raise ValueError(f"Failed to connect or extract schema: {str(e)}")
    finally:
        engine.dispose()


def clean_sql_string(raw_sql: str) -> str:
    """
    Strips markdown code blocks, conversational preamble/postamble text,
    and isolates the SQL statement (WITH ... or SELECT ...).
    """
    cleaned = re.sub(r"```(?:sql)?", "", raw_sql, flags=re.IGNORECASE)
    cleaned = cleaned.replace("```", "").strip()

    match = re.search(r"((?:WITH|SELECT)\s+.+?)(?:;|\Z)", cleaned, re.IGNORECASE | re.DOTALL)
    if match:
        cleaned = match.group(1) + ";"

    return cleaned.strip()


def generate_sql_query(schema: str, user_prompt: str, gemini_api_key: str) -> str:
    """
    Uses Google Gemini Flash to generate a valid, optimized SQL query
    constrained strictly to the provided database schema.
    """
    client = genai.Client(api_key=gemini_api_key)

    current_date = datetime.date.today().strftime("%Y-%m-%d")
    current_year = datetime.date.today().year

    system_prompt = f"""
You are an expert, strict SQL translation engine.
Your sole job is to translate natural language user requests into valid MySQL SELECT queries based ONLY on the provided schema.

Target Database Schema:
{schema}

Current Reference Date: {current_date} (Year: {current_year})

CRITICAL RULES:
1. Output ONLY the raw MySQL query. Do NOT wrap it in markdown code blocks (no ```sql or ```).
2. Do NOT include explanatory commentary or introductory text.
3. Strictly generate valid MySQL syntax compatible with MySQL 8.0 `sql_mode=ONLY_FULL_GROUP_BY`.
4. When finding duplicate rows, records with same values (e.g. same email on same day/date), use window functions with CTEs like:
   WITH grouped_records AS (
       SELECT *, COUNT(*) OVER(PARTITION BY col1, DATE(date_col)) AS match_count
       FROM table_name
   )
   SELECT * FROM grouped_records WHERE match_count > 1;
   DO NOT use invalid `WHERE (col1, DATE(col2)) IN (SELECT col1, DATE(col2) FROM table GROUP BY col1, DATE(col2) HAVING COUNT(*) > 1)` because MySQL rejects non-aggregated HAVING in subqueries.
5. Use standard ISO date formats ('YYYY-MM-DD') for date range comparisons (e.g. DATE(created_at) BETWEEN '2026-07-25' AND '2026-08-01').
6. If a year is omitted in a date request (e.g., "25th july and 1st august"), default to the current reference year ({current_year}).
7. Do NOT use double quotes (") for column or table names. Use backticks (`) or no quotes.
8. Strictly generate SELECT queries. Never output INSERT, UPDATE, DELETE, or DROP.

EXAMPLES OF CORRECT RESPONSES:
User: Show all bookings from month 8
Output: SELECT * FROM bookings WHERE MONTH(createdAt) = 8;

User: Show bookings between 25th july and 1st august
Output: SELECT * FROM bookings WHERE DATE(createdAt) BETWEEN '{current_year}-07-25' AND '{current_year}-08-01';

User: Find all the records, having bookings from the same email, on the same day
Output: WITH duplicate_bookings AS (SELECT *, COUNT(*) OVER(PARTITION BY email, DATE(createdAt)) AS booking_count FROM bookings) SELECT * FROM duplicate_bookings WHERE booking_count > 1;

User: Find top 5 highest paid employees
Output: SELECT * FROM employees ORDER BY salary DESC LIMIT 5;
"""

    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=user_prompt,
        config=types.GenerateContentConfig(
            max_output_tokens=2048,
            system_instruction=system_prompt,
            temperature=0.0
        )
    )

    return clean_sql_string(response.text)


def validate_sql_query(sql_query: str) -> bool:
    """
    Parses and verifies the SQL query to block destructive commands,
    multiple stacked statements (SQL injection prevention), and ensure
    only read-only SELECT / CTE WITH statements are executed.
    """
    clean_sql = sql_query.strip().rstrip(';')

    parsed = sqlparse.parse(clean_sql)

    if not parsed:
        raise ValueError("Invalid SQL query: Unable to parse.")

    # Security check: Block stacked/multiple statements
    non_empty_stmts = [s for s in parsed if str(s).strip()]
    if len(non_empty_stmts) > 1:
        raise ValueError("Security Block: Multiple SQL statements detected.")

    stmt = non_empty_stmts[0]
    statement_type = stmt.get_type()

    # Normalize query string: strip leading SQL comments, whitespace, and parentheses
    lines = [line.strip() for line in clean_sql.splitlines() if line.strip()]
    while lines and (lines[0].startswith("--") or lines[0].startswith("/*")):
        lines.pop(0)
    sql_no_comments = " ".join(lines).strip().lstrip("(").strip()
    normalized_upper = sql_no_comments.upper()

    # Fallback check if sqlparse marks valid SELECT/WITH as UNKNOWN
    if statement_type == 'UNKNOWN':
        if normalized_upper.startswith("SELECT") or normalized_upper.startswith("WITH"):
            statement_type = 'SELECT'

    if statement_type != 'SELECT' and not normalized_upper.startswith("WITH"):
        raise ValueError(f"Security Block: Expected SELECT statement, got '{statement_type}'.")

    return True


def serialize_row_value(val: Any) -> Any:
    """
    Safely serializes database field types into JSON-compatible values.
    """
    if isinstance(val, (datetime.date, datetime.datetime)):
        return val.isoformat()
    if isinstance(val, bytes):
        return val.decode("utf-8", errors="replace")
    if hasattr(val, "__str__") and type(val).__name__ == "Decimal":
        return float(val)
    return val


@app.get("/", tags=["General"])
async def root():
    return {
        "service": "NL2SQL Engine (Backend-as-a-Service)",
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs",
        "endpoints": {
            "health": "GET /health",
            "query": "POST /query"
        }
    }


@app.get("/health", tags=["General"])
async def health_check():
    return {"status": "healthy", "timestamp": datetime.datetime.utcnow().isoformat()}


@app.post("/query", response_model=QueryResponse, tags=["Query"])
async def query_endpoint(request: QueryRequest):
    """
    Translates a natural language question into SQL using the schema of the
    provided database, validates query safety, executes it, and returns the results.
    """
    engine = None
    try:
        # Step 1: Extract Schema
        schema = extract_database_schema(request.db_connection_uri)
        
        # Step 2: Generate Cleaned SQL Query
        generated_sql = generate_sql_query(schema, request.user_prompt, request.gemini_api_key)

        # Step 3: Validate Query
        validate_sql_query(generated_sql)

        # Step 4: Execute Query
        engine = create_engine(request.db_connection_uri)
        with engine.connect() as connection:
            # Relax ONLY_FULL_GROUP_BY for MySQL to prevent 1055 OperationalError
            if "mysql" in request.db_connection_uri.lower():
                try:
                    connection.execute(text("SET SESSION sql_mode=(SELECT REPLACE(@@sql_mode,'ONLY_FULL_GROUP_BY',''));"))
                except Exception:
                    pass

            result = connection.execute(text(generated_sql))
            rows = [
                {k: serialize_row_value(v) for k, v in dict(row._mapping).items()}
                for row in result
            ]
            
            return {
                "status": "success",
                "sql_query": generated_sql, 
                "row_count": len(rows),
                "data": rows
            }

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution error: {str(e)}")
    finally:
        if engine:
            engine.dispose()
