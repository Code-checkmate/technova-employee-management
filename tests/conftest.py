"""
TechNova Employee Management System — Pytest Fixtures
Sets up isolated in-memory SQLite database and test clients for all tests.
"""

import pytest
from datetime import date
from app import create_app
from config import TestConfig
import database
from models import Employee


@pytest.fixture(scope="function")
def app():
    """Creates a fresh Flask test app instance for each test function."""
    app_instance = create_app(TestConfig)

    with app_instance.app_context():
        # Ensure fresh tables in in-memory SQLite
        database.Base.metadata.drop_all(bind=database.engine)
        database.Base.metadata.create_all(bind=database.engine)
        yield app_instance
        # Clean up session and drop tables
        database.db_session.remove()
        database.Base.metadata.drop_all(bind=database.engine)


@pytest.fixture(scope="function")
def client(app):
    """Provides a test client for simulating HTTP requests."""
    return app.test_client()


@pytest.fixture(scope="function")
def sample_employee(app):
    """Creates a standard test employee in the test database."""
    emp = Employee(
        full_name="Samantha Ray",
        email="samantha.ray@technova.internal",
        department="Database Engineering",
        job_title="Lead Aurora Migration Specialist",
        phone="+1 555-019-9988",
        joining_date=date(2022, 5, 10),
        status="Active",
    )
    database.db_session.add(emp)
    database.db_session.commit()
    database.db_session.refresh(emp)
    return emp
