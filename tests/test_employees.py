"""
TechNova Employee Management System — Employee CRUD and Validation Tests
Tests creation, retrieval, updates, deletion, duplicate handling, search, and pagination.
"""

from datetime import date
from database import db_session
from models import Employee


def test_employee_list_loads(client, sample_employee):
    """Verifies that employee directory loads with HTTP 200 and shows existing records."""
    response = client.get("/employees")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Employee Directory" in html
    assert sample_employee.full_name in html
    assert sample_employee.email in html


def test_employee_creation_success(client):
    """Verifies creating a new employee with valid parameters."""
    payload = {
        "full_name": "Tariq Edwards",
        "email": "tariq.edwards@technova.internal",
        "department": "DevOps & SRE",
        "job_title": "Site Reliability Engineer",
        "phone": "+1 555-019-3344",
        "joining_date": "2023-04-15",
        "status": "Active",
    }
    response = client.post("/employees/new", data=payload, follow_redirects=True)
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "successfully added" in html
    assert "Tariq Edwards" in html

    # Verify directly in database
    emp = db_session.query(Employee).filter_by(email="tariq.edwards@technova.internal").first()
    assert emp is not None
    assert emp.full_name == "Tariq Edwards"
    assert emp.department == "DevOps & SRE"
    assert emp.status == "Active"


def test_employee_retrieval_detail(client, sample_employee):
    """Verifies that an existing employee detail page loads successfully."""
    response = client.get(f"/employees/{sample_employee.id}")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert sample_employee.full_name in html
    assert sample_employee.email in html
    assert sample_employee.job_title in html
    assert "Database Record Metadata" in html


def test_missing_employee_returns_404(client):
    """Verifies that requesting a nonexistent employee returns HTTP 404."""
    response = client.get("/employees/999999")
    assert response.status_code == 404
    html = response.data.decode("utf-8")
    assert "Record or Page Not Found" in html


def test_employee_update_success(client, sample_employee):
    """Verifies updating an existing employee's details."""
    payload = {
        "full_name": "Samantha Ray-Chen",
        "email": sample_employee.email,  # Keeping same email
        "department": "Cloud Architecture",
        "job_title": "Principal Aurora Architect",
        "phone": "+1 555-019-7722",
        "joining_date": "2022-05-10",
        "status": "Active",
    }
    response = client.post(f"/employees/{sample_employee.id}/edit", data=payload, follow_redirects=True)
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "updated successfully" in html
    assert "Samantha Ray-Chen" in html

    # Verify database state
    db_session.refresh(sample_employee)
    assert sample_employee.full_name == "Samantha Ray-Chen"
    assert sample_employee.department == "Cloud Architecture"
    assert sample_employee.job_title == "Principal Aurora Architect"


def test_duplicate_email_rejected_on_create(client, sample_employee):
    """Verifies that submitting a duplicate email on create is rejected with validation message."""
    payload = {
        "full_name": "Imposter Employee",
        "email": sample_employee.email,  # Duplicate email!
        "department": "Software Development",
        "job_title": "Software Engineer",
        "phone": "+1 555-111-2222",
        "joining_date": "2023-01-01",
        "status": "Active",
    }
    response = client.post("/employees/new", data=payload, follow_redirects=True)
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "already registered" in html

    # Verify imposter was NOT saved
    count = db_session.query(Employee).filter_by(full_name="Imposter Employee").count()
    assert count == 0


def test_invalid_input_validation(client):
    """Verifies that empty required fields and malformed emails are rejected."""
    payload = {
        "full_name": "",  # Missing required
        "email": "not-a-valid-email",  # Invalid email format
        "department": "",
        "job_title": "",
        "joining_date": "invalid-date",
        "status": "Active",
    }
    response = client.post("/employees/new", data=payload, follow_redirects=True)
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Full name is required." in html
    assert "valid email address" in html
    assert "Please select a valid department." in html


def test_employee_delete_via_post(client, sample_employee):
    """Verifies that employee is deleted via a POST request."""
    emp_id = sample_employee.id
    response = client.post(f"/employees/{emp_id}/delete", follow_redirects=True)
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "successfully deleted" in html

    # Verify employee is gone from database
    deleted_emp = db_session.get(Employee, emp_id)
    assert deleted_emp is None


def test_delete_missing_employee_returns_404(client):
    """Verifies that attempting to delete a nonexistent employee returns HTTP 404."""
    response = client.post("/employees/999999/delete")
    assert response.status_code == 404


def test_search_and_filtering(client, sample_employee):
    """Verifies search by name/email and filtering by department and status."""
    # Add a second distinct employee
    emp2 = Employee(
        full_name="Nadia Lindqvist",
        email="nadia.lindqvist@technova.internal",
        department="Software Development",
        job_title="Frontend Engineer",
        phone=None,
        joining_date=date(2023, 7, 1),
        status="Inactive",
    )
    db_session.add(emp2)
    db_session.commit()

    # Search by keyword matching sample_employee
    resp_search = client.get("/employees?q=Samantha")
    assert resp_search.status_code == 200
    html_search = resp_search.data.decode("utf-8")
    assert "Samantha Ray" in html_search
    assert "Nadia Lindqvist" not in html_search

    # Filter by department
    resp_dept = client.get("/employees?department=Software+Development")
    assert resp_dept.status_code == 200
    html_dept = resp_dept.data.decode("utf-8")
    assert "Nadia Lindqvist" in html_dept
    assert "Samantha Ray" not in html_dept

    # Filter by status
    resp_status = client.get("/employees?status=Inactive")
    assert resp_status.status_code == 200
    html_status = resp_status.data.decode("utf-8")
    assert "Nadia Lindqvist" in html_status
    assert "Samantha Ray" not in html_status


def test_pagination_functionality(client):
    """Verifies pagination divides records correctly across pages."""
    # Seed 15 employees
    for i in range(15):
        emp = Employee(
            full_name=f"Batch Worker {i+1:02d}",
            email=f"worker.{i+1}@technova.internal",
            department="Cloud Architecture",
            job_title="Cloud Engineer",
            joining_date=date(2022, 1, 1),
            status="Active",
        )
        db_session.add(emp)
    db_session.commit()

    # Page 1 with per_page=10
    resp_p1 = client.get("/employees?page=1&per_page=10")
    assert resp_p1.status_code == 200
    html_p1 = resp_p1.data.decode("utf-8")
    assert "Batch Worker 01" in html_p1
    assert "Showing page 1 of 2" in html_p1

    # Page 2
    resp_p2 = client.get("/employees?page=2&per_page=10")
    assert resp_p2.status_code == 200
    html_p2 = resp_p2.data.decode("utf-8")
    assert "Batch Worker 15" in html_p2
    assert "Showing page 2 of 2" in html_p2
