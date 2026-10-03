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