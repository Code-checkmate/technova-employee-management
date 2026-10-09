"""
TechNova Employee Management System — Health & Diagnostic Endpoint Tests
Verifies /health probe returns HTTP 200 on healthy database and handles failures
truthfully without exposing database credentials, secrets, or internal traces.
"""

from app import create_app
from config import Config
from database import check_db_connectivity


def test_health_endpoint_healthy(client):
    """Verifies that /health returns HTTP 200 and truthful JSON when database is operational."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()

    assert data is not None
    assert data["status"] == "UP"
    assert data["database_connected"] is True
    assert data["database_mode"] == "sqlite"
    assert data["engine_type"] == "SQLite (In-Memory)"
    assert data["dialect"] == "sqlite"
    assert data["database_name"] == ":memory:"
    assert "latency_ms" in data
    assert "checked_at" in data
    assert "password" not in str(data).lower()


def test_health_endpoint_failure_handling_and_no_secrets_exposed():
    """
    Verifies that when database connectivity fails:
    1. Returns HTTP 503.
    2. JSON payload reports status='DOWN' and database_connected=False.
    3. Sensitive passwords, raw connection strings, or full stack traces are NEVER exposed.
    """
    secret_pass = "SuperSecretDbPassword123!"

    class FailingDbConfig(Config):
        TESTING = True
        DATABASE_MODE = "mysql"
        MYSQL_HOST = "192.0.2.1"  # Non-routable TEST-NET-1 IP address
        MYSQL_PORT = 3306
        MYSQL_DATABASE = "technova_test_db"
        MYSQL_USER = "technova_admin"
        MYSQL_PASSWORD = secret_pass
        MYSQL_CONNECT_TIMEOUT = 1  # 1 second timeout for fast failure

    app_failing = create_app(FailingDbConfig)
    with app_failing.test_client() as test_client:
        response = test_client.get("/health")
        # Must return non-200 response when database is unreachable
        assert response.status_code == 503
        data = response.get_json()

        assert data is not None
        assert data["status"] == "DOWN"
        assert data["database_connected"] is False
        assert data["database_mode"] == "mysql"
        assert data["database_name"] == "technova_test_db"

        # CRITICAL SECURITY CHECK: Ensure password is never exposed
        response_text = response.data.decode("utf-8")
        assert secret_pass not in response_text
        assert "mysql+pymysql://" not in response_text


def test_check_db_connectivity_helper():
    """Verifies the direct database connectivity helper function."""
    status = check_db_connectivity()
    assert isinstance(status, dict)
    assert "connected" in status
    assert "engine_type" in status
    assert "checked_at" in status
