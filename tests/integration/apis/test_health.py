"""Integration tests for the health endpoint."""


def test_health(client):
    """Return a healthy response from the health endpoint."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
