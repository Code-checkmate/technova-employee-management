"""
TechNova Employee Management System — SQLAlchemy Models
Defines the Employee model, indexes, and serialization helpers.
"""

from datetime import datetime, timezone, date
from sqlalchemy import Column, Integer, String, Date, DateTime, Index
from database import Base


class Employee(Base):
    """
    Employee model representing personnel records in the TechNova organization.
    Designed for full compatibility with MySQL 8, Amazon RDS for MySQL,
    Amazon Aurora MySQL, and SQLite.
    """
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(100), nullable=False, index=True)
    email = Column(String(120), nullable=False, unique=True, index=True)
    department = Column(String(80), nullable=False, index=True)
    job_title = Column(String(100), nullable=False)
    phone = Column(String(30), nullable=True)
    joining_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False, default="Active", index=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Composite index for search and department filtering
    __table_args__ = (
        Index("ix_emp_dept_status", "department", "status"),
    )

    def to_dict(self) -> dict:
        """Serializes the employee record into a dictionary."""
        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "department": self.department,
            "job_title": self.job_title,
            "phone": self.phone or "",
            "joining_date": self.joining_date.isoformat() if isinstance(self.joining_date, (date, datetime)) else str(self.joining_date),
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<Employee id={self.id} name='{self.full_name}' dept='{self.department}' status='{self.status}'>"
