# NL2SQL Backend Service

A lightweight, secure Natural Language to SQL Backend-as-a-Service (BaaS) built with **FastAPI**, **SQLAlchemy**, and LLM generation. 

It introspects database schemas on the fly, translates natural language questions into database-compatible SQL, performs strict AST-based security checks, executes the query safely, and returns serialized JSON.

---

## Technical Design & Decisions (Why It's Built This Way)

Translating natural language to SQL in production has significant failure modes: LLM hallucinations, SQL injection, dialect incompatibility, connection leaks, and serialization crashes. Below is the breakdown of decisions taken at each stage of the pipeline and the rationale behind them.

### 1. Dynamic Schema Discovery
- **Decision:** Use `sqlalchemy.inspect(engine)` to extract table names and column datatypes dynamically on each request.
- **Why:** 
  - Avoids manual schema caching or schema drift issues when underlying tables change.
  - Dialect-agnostic: Works consistently across MySQL, PostgreSQL, SQLite, MariaDB, and Oracle without maintaining database-specific catalog queries (`INFORMATION_SCHEMA`, `pg_catalog`, `sqlite_master`).
  - **Connection Safety:** The database engine is explicitly closed in a `finally` block (`engine.dispose()`) after schema extraction and query execution to prevent connection pool exhaustion under concurrent loads.

### 2. Prompt Hardening & Temporal Anchoring
- **Decision:** Inject the current reference date (`YYYY-MM-DD`) and current year into the system instruction, alongside strict SQL generation rules and `temperature=0.0`.
- **Why:**
  - **Temporal Ambiguity:** Queries like *"bookings between 25th July and 1st August"* fail or pick random historical years unless the LLM is explicitly anchored to the current calendar year.
  - **MySQL 8.0 Grouping Constraints:** Standard LLMs often write invalid duplicate-detection queries like `WHERE (col1, col2) IN (SELECT col1, col2 FROM tbl GROUP BY col1 HAVING COUNT(*) > 1)`. In MySQL 8.0 (`ONLY_FULL_GROUP_BY`), non-aggregated expressions in `HAVING` without full group keys trigger fatal syntax errors. The prompt enforces Common Table Expressions (CTEs) with window functions (`COUNT(*) OVER(PARTITION BY ...)`).
  - **Strict Read-Only Generation:** The system prompt explicitly instructs the LLM to output only `SELECT` queries and forbids DDL/DML.

### 3. Regex Isolation & Pre-cleaning
- **Decision:** Multi-stage regex extraction (`clean_sql_string`) that strips markdown fences (````sql ... ````) and isolates the first `SELECT` or `WITH` statement up to the terminating semicolon.
- **Why:**
  - Even with zero-temperature instructions, LLMs occasionally output markdown blocks, explanatory preambles (*"Here is the SQL query:"*), or trailing commentary (*"Note: This filters active records"*).
  - Raw execution of such responses causes database syntax errors. The regex extracts purely the query string.

### 4. AST-Based Security Validation (`sqlparse`)
- **Decision:** Parse the cleaned SQL into an Abstract Syntax Tree (AST) using `sqlparse` instead of basic string matching / keyword blacklists.
- **Why:**
  - **Keyword Blacklist Failure:** Simple checks like `if "DROP" in query` create false positives on columns or tables named `dropped_count` or `order_drops`, and false negatives against nested comments (`-- DROP`).
  - **Stacked Statement / Injection Blocker:** `sqlparse.parse()` tokenizes statements. If `len(non_empty_stmts) > 1`, the query is immediately rejected. This prevents chained execution attacks (e.g. `SELECT * FROM users; DROP TABLE logs;`).
  - **Root Statement Type Verification:** Verifies that the primary statement type is strictly `SELECT` or a `WITH` CTE, rejecting `INSERT`, `UPDATE`, `DELETE`, `ALTER`, `SHOW`, `EXPLAIN`, or `GRANT`.

### 5. MySQL Session Mode Compatibility
- **Decision:** Execute `SET SESSION sql_mode=(SELECT REPLACE(@@sql_mode,'ONLY_FULL_GROUP_BY',''));` at the session level when connecting to MySQL dialects.
- **Why:**
  - MySQL Error 1055 (`Expression not in GROUP BY clause`) frequently fails valid aggregated queries.
  - Rather than requiring administrators to alter global server configurations, modifying the session mode solely for the ephemeral query connection ensures reliable execution without impacting global database policy.

### 6. Safe JSON Serialization
- **Decision:** Custom row serializer (`serialize_row_value`) mapping `datetime.date`, `datetime.datetime`, `Decimal`, and `bytes` into JSON-safe types.
- **Why:**
  - SQLAlchemy raw row results contain Python native objects. Standard `json.dumps` crashes on `Decimal` (common in financial/pricing tables) or `bytes` (BLOBs/UUIDs).
  - Explicit transformation guarantees clean JSON responses across any client language.

---

## Switching LLM Providers

The engine is decoupled from any specific model. You can swap Google Gemini with **OpenAI**, **Anthropic Claude**, or **Ollama / Local LLMs** by adjusting `generate_sql_query` in `main.py`.

The request model accepts both `llm_api_key` (generic) and `gemini_api_key` (backward compatible), or falls back to the `LLM_API_KEY` / `GEMINI_API_KEY` environment variable.

### Option A: Using OpenAI (GPT-4o / GPT-4o-mini)
```bash
pip install openai
```
```python
from openai import OpenAI

def generate_sql_query(schema: str, user_prompt: str, llm_api_key: str) -> str:
    client = OpenAI(api_key=llm_api_key)
    
    system_prompt = build_system_prompt(schema) # same prompt template
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    
    raw_sql = response.choices[0].message.content
    return clean_sql_string(raw_sql)
```

### Option B: Using Anthropic Claude (Claude 3.5 Sonnet)
```bash
pip install anthropic
```
```python
import anthropic

def generate_sql_query(schema: str, user_prompt: str, llm_api_key: str) -> str:
    client = anthropic.Anthropic(api_key=llm_api_key)
    
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2048,
        temperature=0.0,
        system=build_system_prompt(schema),
        messages=[
            {"role": "user", "content": user_prompt}
        ]
    )
    
    raw_sql = response.content[0].text
    return clean_sql_string(raw_sql)
```

### Option C: Using LiteLLM (Universal Multi-Provider Proxy)
```bash
pip install litellm
```
```python
from litellm import completion

def generate_sql_query(schema: str, user_prompt: str, llm_api_key: str) -> str:
    # Supports "gpt-4o", "claude-3-5-sonnet", "ollama/llama3", "gemini/gemini-flash-latest"
    response = completion(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": build_system_prompt(schema)},
            {"role": "user", "content": user_prompt}
        ],
        api_key=llm_api_key,
        temperature=0.0
    )
    return clean_sql_string(response.choices[0].message.content)
```

---

## Quickstart

### 1. Installation
```bash
git clone https://github.com/<your-username>/nl2sql.git
cd nl2sql

python -m venv venv

# Windows:
.\venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Environment Configuration (Optional)
Copy `.env.example` to `.env` if you want to set a default API key or server port:
```env
LLM_API_KEY=your_api_key_here
PORT=8000
HOST=0.0.0.0
```

### 3. Run the Server
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive documentation: `http://localhost:8000/docs`

---

## API Reference

### `POST /query`
Translates a natural language prompt to SQL based on target database schema, validates safety, executes query, and returns results.

#### Request Body
```json
{
  "db_connection_uri": "mysql+pymysql://user:password@localhost:3306/ecommerce_db",
  "user_prompt": "Find top 5 highest spending customers this month",
  "llm_api_key": "YOUR_API_KEY"
}
```

*Note: You can pass either `llm_api_key` or `gemini_api_key`, or omit both if `LLM_API_KEY`/`GEMINI_API_KEY` is set in the server environment.*

#### Response (`200 OK`)
```json
{
  "status": "success",
  "sql_query": "SELECT customer_id, SUM(amount) AS total_spent FROM orders WHERE MONTH(order_date) = 8 GROUP BY customer_id ORDER BY total_spent DESC LIMIT 5;",
  "row_count": 5,
  "data": [
    {
      "customer_id": 104,
      "total_spent": 1250.50
    },
    {
      "customer_id": 89,
      "total_spent": 980.00
    }
  ]
}
```

---

## Testing & Edge Cases

The test suite in `test_edge_cases.py` contains 29 comprehensive test cases verifying:
- Markdown stripping & preamble/postamble removal.
- CTE `WITH` statement preservation.
- SQL injection prevention (stacked query blocking).
- AST security validation (rejecting `DROP`, `INSERT`, `UPDATE`, `DELETE`, `EXPLAIN`, `SHOW`).
- Dynamic schema extraction on SQLite/MySQL structures.
- Serialization of non-JSON types (`TIMESTAMP`, `REAL`, `BLOB`).
- Sensitive credential masking in connection error logs.

To run the tests:
```bash
pytest test_edge_cases.py -v
```

---

## License

MIT License. See [LICENSE](LICENSE) for details.
