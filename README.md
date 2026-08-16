# 🚀 NL2SQL Engine (Backend-as-a-Service)

A lightweight, secure, high-performance **Natural Language to SQL Backend-as-a-Service (BaaS)** powered by **Google Gemini Flash**, **FastAPI**, and **SQLAlchemy**.

NL2SQL automatically inspects your database schema, converts natural language questions into valid, optimized SQL queries, applies strict AST-based security checks, executes the query safely, and returns serialized JSON results.

---

## ✨ Features

- 🔍 **Zero-Config Schema Discovery**: Automatically connects to your target database and extracts table names and column definitions dynamically.
- 🧠 **Google Gemini Flash Engine**: Generates precise SQL tailored specifically to your schema with date-awareness, strict MySQL 8.0 compatibility, and window functions / CTE support.
- 🛡️ **Built-in Security Guardrails**:
  - **Read-Only Enforcement**: Strictly blocks destructive DDL/DML (`DROP`, `ALTER`, `INSERT`, `UPDATE`, `DELETE`, `TRUNCATE`, `GRANT`).
  - **Anti-SQL Injection**: Blocks stacked/chained SQL statements (`sqlparse` AST parsing).
  - **SQL Sanitization**: Strips conversational preambles/postambles and markdown artifacts.
- 📊 **Safe JSON Serialization**: Seamlessly serializes Python `datetime`, `Decimal`, `bytes`, and complex SQL types to JSON.
- ⚡ **Interactive Swagger & ReDoc**: Complete OpenAPI documentation available instantly at `/docs` and `/redoc`.

---

## 🛠️ Architecture Flow

```
┌─────────────────┐       ┌────────────────────────┐       ┌───────────────────────┐
│                 │       │                        │       │                       │
│  User Request   ├──────►│   NL2SQL FastAPI App   ├──────►│  Target Database      │
│  (NL + DB URI)  │       │                        │       │  (Schema Inspection)  │
│                 │       └───────────┬────────────┘       └───────────────────────┘
└─────────────────┘                   │
                                      ▼
                          ┌────────────────────────┐
                          │  Google Gemini Flash   │
                          │  (SQL Query Synthesis) │
                          └───────────┬────────────┘
                                      │
                                      ▼
                          ┌────────────────────────┐
                          │  AST Security Check    │
                          │  & Query Validation    │
                          └───────────┬────────────┘
                                      │
                                      ▼
                          ┌────────────────────────┐
                          │  Read-Only Execution   │
                          │  & JSON Serialization  │
                          └────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/<your-username>/nl2sql.git
cd nl2sql
```

### 2. Create and Activate a Virtual Environment
```bash
# On Linux/macOS
python3 -m venv venv
source venv/bin/activate

# On Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Backend Service
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Your API is now running at `http://localhost:8000`.  
Visit **Interactive API Docs** at: `http://localhost:8000/docs`

---

## 📖 API Reference

### 1. Health Check
```http
GET /health
```
**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-08-16T12:30:00.000000"
}
```

---

### 2. Execute NL2SQL Query
```http
POST /query
Content-Type: application/json
```

#### Request Body
| Field | Type | Description |
| :--- | :--- | :--- |
| `db_connection_uri` | `string` | SQLAlchemy connection string (e.g. `mysql+pymysql://user:pass@host:3306/db`, `sqlite:///data.db`) |
| `user_prompt` | `string` | Natural language question or query description |
| `gemini_api_key` | `string` | Google Gemini API Key |

**Example Request:**
```json
{
  "db_connection_uri": "mysql+pymysql://root:password@localhost:3306/ecommerce_db",
  "user_prompt": "Find top 5 highest spending customers this month",
  "gemini_api_key": "YOUR_GEMINI_API_KEY"
}
```

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

## 💻 Client Integration Examples

### cURL
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "db_connection_uri": "sqlite:///test.db",
    "user_prompt": "Show all active users",
    "gemini_api_key": "YOUR_GEMINI_API_KEY"
  }'
```

### Python (`requests`)
```python
import requests

payload = {
    "db_connection_uri": "mysql+pymysql://user:pass@localhost:3306/shop",
    "user_prompt": "Show total revenue by category",
    "gemini_api_key": "YOUR_GEMINI_API_KEY"
}

response = requests.post("http://localhost:8000/query", json=payload)
result = response.json()

print("Executed SQL:", result["sql_query"])
print("Data:", result["data"])
```

### JavaScript / TypeScript (`fetch`)
```javascript
const response = await fetch("http://localhost:8000/query", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    db_connection_uri: "mysql+pymysql://user:pass@localhost:3306/shop",
    user_prompt: "Show total revenue by category",
    gemini_api_key: "YOUR_GEMINI_API_KEY"
  })
});

const data = await response.json();
console.log(data);
```

---

## 🧪 Running Tests

The test suite includes 27+ comprehensive unit and edge-case tests covering SQL sanitization, AST injection defense, CTE parsing, serialization, and error handling.

```bash
pytest test_edge_cases.py -v
```

---

## 🔒 Security Highlights

- **AST Statement Validation**: Uses `sqlparse` to decompose statements into syntax trees, rejecting anything that isn't a pure `SELECT` or `WITH ... SELECT`.
- **Chained Query Defense**: Any payload attempting multi-query execution (e.g. `SELECT 1; DROP TABLE users;`) is immediately rejected before touching the database connection.
- **Connection Isolation**: Database connections and engine pools are scoped and disposed of cleanly per request to avoid connection leaks.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
