import pytest
import sqlite3
import tempfile
import os
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, LargeBinary, text
import datetime

from main import (
    app,
    clean_sql_string,
    validate_sql_query,
    extract_database_schema,
    generate_sql_query,
    QueryRequest
)

client = TestClient(app)

# ==========================================
# 1. SQL CLEANING TESTS (clean_sql_string)
# ==========================================
class TestCleanSqlString:
    def test_strip_markdown_blocks(self):
        raw = "```sql\nSELECT * FROM users;\n```"
        assert clean_sql_string(raw) == "SELECT * FROM users;"

    def test_preamble_text_before_select(self):
        raw = "Here is the SQL query you requested:\nSELECT * FROM users WHERE active = 1;"
        assert clean_sql_string(raw) == "SELECT * FROM users WHERE active = 1;"

    def test_postamble_text_after_select(self):
        raw = "SELECT * FROM users;\nNote: This returns active users."
        cleaned = clean_sql_string(raw)
        assert "Note:" not in cleaned, f"Postamble conversational text was not stripped! Result: '{cleaned}'"

    def test_cte_with_clause(self):
        raw = "WITH active_users AS (SELECT * FROM users WHERE active = 1) SELECT * FROM active_users;"
        cleaned = clean_sql_string(raw)
        assert cleaned.startswith("WITH"), f"CTE 'WITH' clause was stripped! Result: '{cleaned}'"

    def test_multiple_select_statements(self):
        raw = "SELECT * FROM users; SELECT * FROM orders;"
        cleaned = clean_sql_string(raw)
        assert cleaned == "SELECT * FROM users;"

    def test_no_select_in_raw(self):
        raw = "DROP TABLE users;"
        assert clean_sql_string(raw) == "DROP TABLE users;"


# ==========================================
# 2. SQL VALIDATION TESTS (validate_sql_query)
# ==========================================
class TestValidateSqlQuery:
    def test_standard_select_valid(self):
        assert validate_sql_query("SELECT * FROM users;") is True

    def test_select_with_leading_spaces_and_newlines(self):
        assert validate_sql_query("   \n\t SELECT * FROM users;") is True

    def test_select_with_leading_comment(self):
        sql = "-- Fetch all active users\nSELECT * FROM users;"
        try:
            res = validate_sql_query(sql)
            assert res is True
        except ValueError as e:
            pytest.fail(f"Valid query with leading comment failed validation: {e}")

    def test_parenthesized_select(self):
        sql = "(SELECT * FROM users);"
        try:
            res = validate_sql_query(sql)
            assert res is True
        except ValueError as e:
            pytest.fail(f"Valid parenthesized SELECT failed validation: {e}")

    def test_cte_with_clause_validation(self):
        sql = "WITH summary AS (SELECT department_id, COUNT(*) as cnt FROM employees GROUP BY department_id) SELECT * FROM summary;"
        try:
            res = validate_sql_query(sql)
            assert res is True
        except ValueError as e:
            pytest.fail(f"Valid CTE query failed validation: {e}")

    def test_security_stacked_queries_injection(self):
        sql = "SELECT * FROM users; DROP TABLE users;"
        with pytest.raises(ValueError, match="Security Block|Multiple statements"):
            validate_sql_query(sql)

    def test_security_stacked_queries_with_comment(self):
        sql = "SELECT 1; -- comment\nDELETE FROM users;"
        with pytest.raises(ValueError, match="Security Block|Multiple statements"):
            validate_sql_query(sql)

    def test_security_drop_table(self):
        with pytest.raises(ValueError):
            validate_sql_query("DROP TABLE users;")

    def test_security_insert_into(self):
        with pytest.raises(ValueError):
            validate_sql_query("INSERT INTO users (id, name) VALUES (1, 'alice');")

    def test_security_update(self):
        with pytest.raises(ValueError):
            validate_sql_query("UPDATE users SET admin = 1;")

    def test_security_delete(self):
        with pytest.raises(ValueError):
            validate_sql_query("DELETE FROM users;")

    def test_security_show_tables(self):
        with pytest.raises(ValueError):
            validate_sql_query("SHOW TABLES;")

    def test_security_explain_select(self):
        with pytest.raises(ValueError):
            validate_sql_query("EXPLAIN SELECT * FROM users;")


# ==========================================
# 3. SCHEMA EXTRACTION TESTS (extract_database_schema)
# ==========================================
class TestExtractDatabaseSchema:
    def test_invalid_db_uri(self):
        with pytest.raises(ValueError, match="Failed to connect or extract schema"):
            extract_database_schema("postgresql://invalid_user:invalid_pass@localhost:9999/fake_db")

    def test_empty_database_schema(self, tmp_path):
        db_file = tmp_path / "empty.db"
        uri = f"sqlite:///{db_file}"
        engine = create_engine(uri)
        engine.connect().close()

        schema = extract_database_schema(uri)
        assert schema == ""

    def test_schema_with_sample_table(self, tmp_path):
        db_file = tmp_path / "test.db"
        uri = f"sqlite:///{db_file}"
        engine = create_engine(uri)
        
        with engine.connect() as conn:
            conn.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT NOT NULL)"))
            conn.commit()

        schema = extract_database_schema(uri)
        assert "Table: users" in schema
        assert "id" in schema
        assert "username" in schema


# ==========================================
# 4. DATA SERIALIZATION & EXECUTION TESTS (/query)
# ==========================================
class TestDataSerializationAndExecution:
    @pytest.fixture
    def setup_db_with_complex_types(self, tmp_path):
        db_file = tmp_path / "complex.db"
        uri = f"sqlite:///{db_file}"
        engine = create_engine(uri)
        
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE test_data (
                    id INTEGER PRIMARY KEY,
                    created_at TIMESTAMP,
                    val_float REAL,
                    data_blob BLOB
                )
            """))
            conn.execute(text("INSERT INTO test_data VALUES (1, '2026-08-02 12:00:00', 99.95, 'binary_data')"))
            conn.commit()
        return uri

    @patch("main.generate_sql_query")
    def test_non_json_serializable_data_types(self, mock_gen_sql, setup_db_with_complex_types):
        mock_gen_sql.return_value = "SELECT * FROM test_data;"
        
        payload = {
            "db_connection_uri": setup_db_with_complex_types,
            "user_prompt": "Get test data",
            "gemini_api_key": "dummy_key"
        }
        
        response = client.post("/query", json=payload)
        assert response.status_code == 200, f"Failed with status {response.status_code}: {response.text}"
        data = response.json()
        assert data["status"] == "success"
        assert len(data["data"]) == 1

    @patch("main.generate_sql_query")
    def test_empty_result_set(self, mock_gen_sql, setup_db_with_complex_types):
        mock_gen_sql.return_value = "SELECT * FROM test_data WHERE id = 999;"
        
        payload = {
            "db_connection_uri": setup_db_with_complex_types,
            "user_prompt": "Get non existent item",
            "gemini_api_key": "dummy_key"
        }
        
        response = client.post("/query", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["row_count"] == 0
        assert data["data"] == []

    @patch("main.generate_sql_query")
    def test_stacked_query_execution_in_endpoint(self, mock_gen_sql, setup_db_with_complex_types):
        mock_gen_sql.return_value = "SELECT * FROM test_data; DROP TABLE test_data;"
        
        payload = {
            "db_connection_uri": setup_db_with_complex_types,
            "user_prompt": "Get data and drop table",
            "gemini_api_key": "dummy_key"
        }
        
        response = client.post("/query", json=payload)
        assert response.status_code == 400

    def test_root_endpoint(self):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["service"] == "NL2SQL Engine (Backend-as-a-Service)"

    def test_health_endpoint(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


# ==========================================
# 5. ENDPOINT ERROR HANDLING & INFORMATION DISCLOSURE
# ==========================================
class TestEndpointErrorHandling:
    def test_missing_payload_fields(self):
        response = client.post("/query", json={"user_prompt": "test"})
        assert response.status_code == 422

    def test_connection_error_handling(self):
        payload = {
            "db_connection_uri": "sqlite:///non_existent_directory_12345/database.db",
            "user_prompt": "Show users",
            "gemini_api_key": "dummy"
        }
        response = client.post("/query", json=payload)
        assert response.status_code in [400, 500]
