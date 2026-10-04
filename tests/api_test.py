from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_sql_query():
    response = client.post(
        "/query",
        json={
            "question": "How many documents mention shipping?"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "answer" in data
    assert "3" in data["answer"]


def test_rag_query():
    response = client.post(
        "/query",
        json={
            "question": "What is the refund period?"
        }
    )

    assert response.status_code == 200

    data = response.json()

    

    assert "answer" in data
    assert "30 days" in data["answer"]


def test_empty_question():

    response = client.post(
        "/query",
        json={
            "question": ""
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Question cannot be empty."

from unittest.mock import patch


def test_query_failure():

    with patch(
        "app.main.graph.invoke",
        side_effect=Exception("Test failure")
    ):
        response = client.post(
            "/query",
            json={
                "question": "Test failure"
            }
        )

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to process the query."