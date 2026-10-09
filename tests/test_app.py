"""
TechNova Employee Management System — Application Route & Security Tests
Tests for dashboard rendering, navigation, 404 handling, and CSRF protection.
"""

from app import create_app
from config import Config


def test_index_redirects_to_dashboard(client):
    """Verifies that the root path redirects cleanly to /dashboard."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert "/dashboard" in response.headers["Location"]


def test_dashboard_loads_successfully(client, sample_employee):
    """Verifies that the dashboard loads with HTTP 200 and renders dynamic statistics."""
    response = client.get("/dashboard")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Executive Dashboard" in html
    assert "Total Employees" in html
    # Should display the sample employee
    assert sample_employee.full_name in html
    assert sample_employee.department in html


def test_database_status_page_loads(client):
    """Verifies that the database diagnostics status page renders with HTTP 200."""
    response = client.get("/database-status")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Database Connection Diagnostics" in html
    assert "Configured Mode" in html
    assert "ONLINE" in html


def test_migration_info_page_loads(client):
    """Verifies that the migration architecture guide renders with HTTP 200."""
    response = client.get("/migration-info")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "AWS Database Migration Architecture" in html
    assert "7-Phase Migration Implementation Plan" in html
    assert "Data Migration Verification Checklist" in html


def test_404_page_not_found(client):
    """Verifies that an unknown route returns custom 404 template with status code 404."""
    response = client.get("/nonexistent-endpoint-test-404")
    assert response.status_code == 404
    html = response.data.decode("utf-8")
    assert "Record or Page Not Found" in html


def test_csrf_protection_enforcement():
    """Verifies that CSRF protection rejects state-changing POST requests when CSRF is active."""
    class CsrfActiveConfig(Config):
        TESTING = True
        WTF_CSRF_ENABLED = True
        DATABASE_MODE = "sqlite"

        @classmethod
        def get_database_uri(cls):
            return "sqlite:///:memory:"

    csrf_app = create_app(CsrfActiveConfig)
    with csrf_app.test_client() as csrf_client:
        # Attempt to POST without CSRF token
        response = csrf_client.post(
            "/employees/new",
            data={
                "full_name": "Unauthenticated Post",
                "email": "csrf.test@technova.internal",
                "department": "Cybersecurity",
                "job_title": "Security Analyst",
                "joining_date": "2023-01-01",
                "status": "Active",
            },
            follow_redirects=True,
        )
        # With CSRF enabled and no token, the request should be rejected / flash CSRF warning
        html = response.data.decode("utf-8")
        assert "security token has expired" in html.lower() or response.status_code == 400
