"""
TechNova Employee Management System — Form Validation
Implements robust server-side validation using Flask-WTF and WTForms.
"""

import re
from datetime import date
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField, SubmitField
from wtforms.validators import (
    DataRequired,
    Email,
    Length,
    Optional,
    ValidationError,
)
from database import db_session
from models import Employee

DEPARTMENTS = [
    ("Cloud Architecture", "Cloud Architecture"),
    ("Database Engineering", "Database Engineering"),
    ("Software Development", "Software Development"),
    ("DevOps & SRE", "DevOps & SRE"),
    ("Cybersecurity", "Cybersecurity"),
    ("Product Management", "Product Management"),
    ("Human Resources", "Human Resources"),
    ("Finance & Accounting", "Finance & Accounting"),
    ("Customer Operations", "Customer Operations"),
]

STATUS_CHOICES = [
    ("Active", "Active"),
    ("Inactive", "Inactive"),
]


class EmployeeForm(FlaskForm):
    """Form for creating and editing employee records."""

    full_name = StringField(
        "Full Name",
        validators=[
            DataRequired(message="Full name is required."),
            Length(min=2, max=100, message="Full name must be between 2 and 100 characters."),
        ],
        render_kw={"placeholder": "e.g., Jane Doe"},
    )

    email = StringField(
        "Email Address",
        validators=[
            DataRequired(message="Email address is required."),
            Email(message="Please provide a valid email address (e.g. user@technova.com)."),
            Length(max=120, message="Email must not exceed 120 characters."),
        ],
        render_kw={"placeholder": "e.g., jane.doe@technova.com"},
    )

    department = SelectField(
        "Department",
        choices=[("", "-- Select Department --")] + DEPARTMENTS,
        validators=[DataRequired(message="Please select a valid department.")],
    )

    job_title = StringField(
        "Job Title",
        validators=[
            DataRequired(message="Job title is required."),
            Length(min=2, max=100, message="Job title must be between 2 and 100 characters."),
        ],
        render_kw={"placeholder": "e.g., Senior Cloud Engineer"},
    )

    phone = StringField(
        "Phone Number (Optional)",
        validators=[
            Optional(),
            Length(max=30, message="Phone number must not exceed 30 characters."),
        ],
        render_kw={"placeholder": "e.g., +1 (555) 234-5678"},
    )

    joining_date = DateField(
        "Joining Date",
        format="%Y-%m-%d",
        validators=[DataRequired(message="A valid joining date (YYYY-MM-DD) is required.")],
        render_kw={"type": "date"},
    )

    status = SelectField(
        "Employment Status",
        choices=STATUS_CHOICES,
        default="Active",
        validators=[DataRequired(message="Please select an employment status.")],
    )

    submit = SubmitField("Save Employee")

    def __init__(self, original_employee=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_employee = original_employee

    def validate_email(self, field):
        """
        Validates email format and ensures no duplicate email exists in the database,
        accounting for the current employee during edit operations.
        """
        normalized_email = field.data.strip().lower()
        field.data = normalized_email

        query = db_session.query(Employee).filter(Employee.email.ilike(normalized_email))
        if self.original_employee and self.original_employee.id:
            query = query.filter(Employee.id != self.original_employee.id)

        existing = query.first()
        if existing:
            raise ValidationError(f"An employee with email '{field.data}' is already registered.")

    def validate_phone(self, field):
        """Sanitizes phone number and checks for allowable character set."""
        if field.data:
            clean_phone = field.data.strip()
            # Allow digits, spaces, plus, hyphens, and parenthesis
            if not re.match(r"^[\d\+\-\(\)\s\.]+$", clean_phone):
                raise ValidationError("Phone number contains invalid characters.")
            field.data = clean_phone

    def validate_joining_date(self, field):
        """Ensures joining date is a valid date object and within a realistic boundary."""
        if field.data:
            if field.data.year < 1970 or field.data.year > 2099:
                raise ValidationError("Joining date year must be between 1970 and 2099.")
