from app import app


def test_health_endpoint():
    client = app.test_client()
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_analyse_requires_query():
    client = app.test_client()
    response = client.get("/api/analyse")
    assert response.status_code == 400


def test_compare_requires_two_topics():
    client = app.test_client()
    response = client.get("/api/compare?q=Apple")
    assert response.status_code == 400
