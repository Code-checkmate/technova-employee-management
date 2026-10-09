"""
TechNova Employee Management System — Demonstration Data Seeder
Explicitly seeds demonstration employee records without truncating,
dropping, or overwriting existing data. Refuses duplicate emails.
"""

import sys
from datetime import date
from sqlalchemy.exc import IntegrityError
from config import Config
from database import create_app_engine, Base
from sqlalchemy.orm import sessionmaker
from models import Employee

SAMPLE_EMPLOYEES = [
    {
        "full_name": "Amina Al-Mansoor",
        "email": "amina.mansoor@technova.internal",
        "department": "Cloud Architecture",
        "job_title": "Principal Solutions Architect",
        "phone": "+1 (555) 019-2831",
        "joining_date": date(2021, 3, 15),
        "status": "Active",
    },
    {
        "full_name": "Marcus Vance",
        "email": "marcus.vance@technova.internal",
        "department": "Database Engineering",
        "job_title": "Lead Database Migration Specialist",
        "phone": "+1 (555) 019-4820",
        "joining_date": date(2020, 8, 1),
        "status": "Active",
    },
    {
        "full_name": "Elena Rostova",
        "email": "elena.rostova@technova.internal",
        "department": "Software Development",
        "job_title": "Staff Backend Engineer",
        "phone": "+1 (555) 019-7712",
        "joining_date": date(2022, 1, 10),
        "status": "Active",
    },
    {
        "full_name": "Devon Zhang",
        "email": "devon.zhang@technova.internal",
        "department": "DevOps & SRE",
        "job_title": "Site Reliability Engineer",
        "phone": "+1 (555) 019-9943",
        "joining_date": date(2022, 6, 20),
        "status": "Active",
    },
    {
        "full_name": "Sarah Jenkins",
        "email": "sarah.jenkins@technova.internal",
        "department": "Cybersecurity",
        "job_title": "Information Security Analyst",
        "phone": "+1 (555) 019-3388",
        "joining_date": date(2023, 2, 1),
        "status": "Active",
    },
    {
        "full_name": "Carlos Gomez",
        "email": "carlos.gomez@technova.internal",
        "department": "Product Management",
        "job_title": "Senior Technical Product Manager",
        "phone": "+1 (555) 019-5561",
        "joining_date": date(2021, 11, 8),
        "status": "Active",
    },
    {
        "full_name": "Rachel Zhao",
        "email": "rachel.zhao@technova.internal",
        "department": "Human Resources",
        "job_title": "People Operations Director",
        "phone": "+1 (555) 019-6124",
        "joining_date": date(2019, 5, 4),
        "status": "Active",
    },
    {
        "full_name": "Liam Gallagher",
        "email": "liam.gallagher@technova.internal",
        "department": "Finance & Accounting",
        "job_title": "Senior Financial Systems Analyst",
        "phone": "+1 (555) 019-8230",
        "joining_date": date(2022, 9, 14),
        "status": "Active",
    },
    {
        "full_name": "Priya Patel",
        "email": "priya.patel@technova.internal",
        "department": "Database Engineering",
        "job_title": "Aurora MySQL Optimization Engineer",
        "phone": "+1 (555) 019-1456",
        "joining_date": date(2023, 4, 17),
        "status": "Active",
    },
    {
        "full_name": "Kofi Mensah",
        "email": "kofi.mensah@technova.internal",
        "department": "Customer Operations",
        "job_title": "Customer Success Engineer",
        "phone": "+1 (555) 019-7329",
        "joining_date": date(2020, 10, 12),
        "status": "Inactive",
    },
    {
        "full_name": "Nadia Lindqvist",
        "email": "nadia.lindqvist@technova.internal",
        "department": "Software Development",
        "job_title": "Frontend Systems Engineer",
        "phone": "+1 (555) 019-2509",
        "joining_date": date(2023, 8, 22),
        "status": "Active",
    },
    {
        "full_name": "Tariq Edwards",
        "email": "tariq.edwards@technova.internal",
        "department": "DevOps & SRE",
        "job_title": "Infrastructure Automation Engineer",
        "phone": "+1 (555) 019-6012",
        "joining_date": date(2021, 7, 19),
        "status": "Inactive",
    },
]


def seed_database(config_class=Config, quiet=False):
    """
    Seeds demonstration data into the configured database.
    Will NOT erase, overwrite, or truncate existing data.
    Skips records if the email already exists.
    """
    engine = create_app_engine(config_class)
    # Ensure tables exist without dropping
    Base.metadata.create_all(bind=engine)

    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = Session()

    inserted_count = 0
    skipped_count = 0

    try:
        for emp_data in SAMPLE_EMPLOYEES:
            existing = session.query(Employee).filter(
                Employee.email == emp_data["email"]
            ).first()

            if existing:
                skipped_count += 1
                continue

            employee = Employee(**emp_data)
            session.add(employee)
            inserted_count += 1

        session.commit()
        if not quiet:
            print("==================================================")
            print("TechNova Employee Management System — Database Seeder")
            print("==================================================")
            print(f"Target Database Engine: {config_class.get_safe_db_info()['engine_type']}")
            print(f"Inserted: {inserted_count} new records")
            print(f"Skipped:  {skipped_count} existing records (duplicates prevented)")
            print("Database seeding completed safely without data loss.")
            print("==================================================")
        return {"inserted": inserted_count, "skipped": skipped_count}

    except Exception as e:
        session.rollback()
        if not quiet:
            print(f"Seeding failed: {e}", file=sys.stderr)
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_database()
