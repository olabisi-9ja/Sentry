import pytest
from fastapi.testclient import TestClient
from app import app
from database.init_db import init_db
import os

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    os.environ["DATABASE_URL"] = ""  # Force SQLite for tests
    init_db()
    yield

client = TestClient(app)

def test_get_communities():
    response = client.get("/api/communities")
    assert response.status_code == 200
    data = response.json()
    assert "communities" in data
    assert len(data["communities"]) >= 3
    assert any(c["community_id"] == "kwasu_main" for c in data["communities"])

def test_post_report():
    response = client.post("/api/reports", json={
        "text": "There is a water leak at Hostel Block A",
        "location": "Hostel Block A",
        "community_id": "kwasu_main",
        "anonymous": True,
        "source_type": "web"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "report" in data
    assert data["report"]["category"] == "water"
    assert data["report"]["location"] == "Hostel Block A"

def test_get_reports():
    response = client.get("/api/reports?community_id=kwasu_main")
    assert response.status_code == 200
    data = response.json()
    assert "reports" in data
    assert data["count"] > 0

def test_get_reports_no_query_param():
    response = client.get("/api/reports")
    assert response.status_code == 200

def test_ask_rag():
    response = client.post("/api/ask", json={
        "question": "What is going on with the water at Hostel Block A?",
        "community_id": "kwasu_main"
    })
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert data["confidence_score"] >= 0

def test_situation_room():
    response = client.get("/api/situation-room?community_id=kwasu_main")
    assert response.status_code == 200
    data = response.json()
    assert "summary_bullets" in data
    assert "overall_status" in data

def test_whatsapp_simulate():
    response = client.post("/api/whatsapp/simulate", data={
        "From": "whatsapp:+2348123456789",
        "Body": "Is there any news about the water leak?",
        "community_id": "kwasu_main"
    })
    assert response.status_code == 200
    data = response.json()
    assert "whatsapp_reply" in data
    assert len(data["whatsapp_reply"]) > 0

def test_twilio_webhook():
    response = client.post("/webhook/twilio", data={
        "From": "whatsapp:+2349000000000",
        "Body": "Help there is a fire!"
    })
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/xml"
    assert "<Response></Response>" in response.text
