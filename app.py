"""
TechNova Employee Management System — Main Flask Application
Enterprise demonstration platform for AWS RDS MySQL to Amazon Aurora MySQL migration.
"""

import math
import os
from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    request,
    flash,
    jsonify,
    abort,
)
from flask_wtf.csrf import CSRFProtect, CSRFError
from sqlalchemy import func, or_
from config import Config
from database import init_app_db, db_session, check_db_connectivity
from models import Employee
from forms import EmployeeForm
from seed_data import seed_database

csrf = CSRFProtect()


def create_app(config_class=Config):
    """Application factory for TechNova Employee Management System."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize CSRF Protection
    csrf.init_app(app)

    # Initialize Database and Scoped Session
    init_app_db(app, config_class)

    # -------------------------------------------------------------------------
    # CLI Commands
    # -------------------------------------------------------------------------
    @app.cli.command("seed-db")
    def seed_db_command():
        """Seeds demonstration employee records safely."""
        result = seed_database(config_class=config_class)
        print(f"Seed complete: {result['inserted']} inserted, {result['skipped']} skipped.")

    @app.cli.command("init-db")
    def init_db_command():
        """Initializes database tables safely without dropping data."""
        from database import Base, engine
        Base.metadata.create_all(bind=engine)
        print("Database tables initialized successfully.")

    # -------------------------------------------------------------------------
    # Context Processors & Template Helpers
    # -------------------------------------------------------------------------
    @app.context_processor
    def inject_global_data():
        """Provides application metadata to all templates."""
        return {
            "app_title": "TechNova Employee Management",
            "db_mode": config_class.DATABASE_MODE,
            "is_mysql": config_class.DATABASE_MODE == "mysql",
        }

    # -------------------------------------------------------------------------
    # Error Handlers
    # -------------------------------------------------------------------------
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        # Do not expose internal traces
        app.logger.error(f"Internal server error: {e}")
        return render_template("500.html"), 500

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        flash("Your session or security token has expired. Please refresh the page and try again.", "danger")
        return redirect(request.referrer or url_for("dashboard"))

    # -------------------------------------------------------------------------
    # Health & Database Status Routes
    # -------------------------------------------------------------------------
    @app.route("/health")
    def health_check():
        """
        Lightweight health check endpoint.
        Returns HTTP 200 when database is healthy, HTTP 503 when disconnected.
        Never reveals passwords, full connection strings, or internal traces.
        """
        health = check_db_connectivity(config_class)
        status_code = 200 if health["connected"] else 503
        response_payload = {
            "status": "UP" if health["connected"] else "DOWN",
            "database_connected": health["connected"],
            "database_mode": health["mode"],
            "engine_type": health["engine_type"],
            "dialect": health["dialect"],
            "database_name": health["database_name"],
            "latency_ms": health.get("latency_ms"),
            "checked_at": health["checked_at"],
        }
        if not health["connected"]:
            response_payload["error_summary"] = health.get("error", "Database connection failed")
        return jsonify(response_payload), status_code

    @app.route("/database-status")
    def database_status():
        """Displays rich database connectivity and architecture status."""
        health = check_db_connectivity(config_class)

        # Get total counts if connected
        table_exists = False
        employee_count = 0
        if health["connected"]:
            try:
                employee_count = db_session.query(func.count(Employee.id)).scalar() or 0
                table_exists = True
            except Exception:
                table_exists = False

        return render_template(
            "database_status.html",
            health=health,
            table_exists=table_exists,
            employee_count=employee_count,
            page_title="Database Connection Status",
        )

    @app.route("/migration-info")
    def migration_info():
        """Displays AWS RDS MySQL to Aurora MySQL migration workflow and validation."""
        return render_template(
            "migration_info.html",
            page_title="AWS RDS to Aurora Migration Architecture",
        )

    # -------------------------------------------------------------------------
    # Dashboard Route
    # -------------------------------------------------------------------------
    @app.route("/")
    def index():
        return redirect(url_for("dashboard"))

    @app.route("/dashboard")
    def dashboard():
        """Dashboard displaying real-time metrics and recent employees."""
        health = check_db_connectivity(config_class)

        total_employees = 0
        active_employees = 0
        inactive_employees = 0
        department_count = 0
        recent_employees = []
        dept_breakdown = []

        if health["connected"]:
            try:
                total_employees = db_session.query(func.count(Employee.id)).scalar() or 0
                active_employees = (
                    db_session.query(func.count(Employee.id))
                    .filter(Employee.status == "Active")
                    .scalar() or 0
                )
                inactive_employees = (
                    db_session.query(func.count(Employee.id))
                    .filter(Employee.status == "Inactive")
                    .scalar() or 0
                )
                department_count = (
                    db_session.query(func.count(func.distinct(Employee.department)))
                    .scalar() or 0
                )

                # Department breakdown for chart / progress bars
                dept_breakdown = (
                    db_session.query(Employee.department, func.count(Employee.id))
                    .group_by(Employee.department)
                    .order_by(func.count(Employee.id).desc())
                    .all()
                )

                # 5 Most recently updated or added employees
                recent_employees = (
                    db_session.query(Employee)
                    .order_by(Employee.created_at.desc(), Employee.id.desc())
                    .limit(5)
                    .all()
                )
            except Exception as e:
                app.logger.warning(f"Error querying dashboard metrics: {e}")

        return render_template(
            "dashboard.html",
            total_employees=total_employees,
            active_employees=active_employees,
            inactive_employees=inactive_employees,
            department_count=department_count,
            recent_employees=recent_employees,
            dept_breakdown=dept_breakdown,
            db_connected=health["connected"],
            page_title="Executive Dashboard",
        )

    # -------------------------------------------------------------------------
    # Employee Management Routes (CRUD)
    # -------------------------------------------------------------------------
    @app.route("/employees")
    def employee_list():
        """Paginated list of employees with search and department/status filtering."""
        search_query = request.args.get("q", "").strip()
        selected_dept = request.args.get("department", "").strip()
        selected_status = request.args.get("status", "").strip()
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)

        if page < 1:
            page = 1
        if per_page not in (5, 10, 25, 50):
            per_page = 10

        query = db_session.query(Employee)

        if search_query:
            search_pattern = f"%{search_query}%"
            query = query.filter(
                or_(
                    Employee.full_name.ilike(search_pattern),
                    Employee.email.ilike(search_pattern),
                    Employee.job_title.ilike(search_pattern),
                )
            )

        if selected_dept:
            query = query.filter(Employee.department == selected_dept)

        if selected_status in ("Active", "Inactive"):
            query = query.filter(Employee.status == selected_status)

        # Get total matching count
        total_items = query.count()
        total_pages = max(1, math.ceil(total_items / per_page))
        if page > total_pages and total_items > 0:
            page = total_pages

        offset = (page - 1) * per_page
        employees = (
            query.order_by(Employee.full_name.asc())
            .offset(offset)
            .limit(per_page)
            .all()
        )

        # Fetch distinct departments for filter dropdown
        departments = [
            d[0] for d in db_session.query(func.distinct(Employee.department))
            .order_by(Employee.department.asc())
            .all()
            if d[0]
        ]

        return render_template(
            "employees.html",
            employees=employees,
            total_items=total_items,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            search_query=search_query,
            selected_dept=selected_dept,
            selected_status=selected_status,
            departments=departments,
            page_title="Employee Directory",
        )

    @app.route("/employees/<int:id>")
    def employee_detail(id):
        """Displays full details of a specific employee."""
        employee = db_session.get(Employee, id)
        if not employee:
            abort(404)
        return render_template(
            "employee_detail.html",
            employee=employee,
            page_title=f"Employee: {employee.full_name}",
        )

    @app.route("/employees/new", methods=["GET", "POST"])
    def employee_create():
        """Creates a new employee record with validation."""
        form = EmployeeForm()

        if form.validate_on_submit():
            new_employee = Employee(
                full_name=form.full_name.data.strip(),
                email=form.email.data.strip().lower(),
                department=form.department.data,
                job_title=form.job_title.data.strip(),
                phone=form.phone.data.strip() if form.phone.data else None,
                joining_date=form.joining_date.data,
                status=form.status.data,
            )
            try:
                db_session.add(new_employee)
                db_session.commit()
                flash(f"Employee '{new_employee.full_name}' was successfully added.", "success")
                return redirect(url_for("employee_detail", id=new_employee.id))
            except Exception as e:
                db_session.rollback()
                app.logger.error(f"Failed to add employee: {e}")
                flash("An error occurred while saving the employee record. Please try again.", "danger")

        return render_template(
            "employee_form.html",
            form=form,
            action="create",
            page_title="Add New Employee",
        )

    @app.route("/employees/<int:id>/edit", methods=["GET", "POST"])
    def employee_edit(id):
        """Updates an existing employee record with validation."""
        employee = db_session.get(Employee, id)
        if not employee:
            abort(404)

        form = EmployeeForm(original_employee=employee, obj=employee)

        if form.validate_on_submit():
            employee.full_name = form.full_name.data.strip()
            employee.email = form.email.data.strip().lower()
            employee.department = form.department.data
            employee.job_title = form.job_title.data.strip()
            employee.phone = form.phone.data.strip() if form.phone.data else None
            employee.joining_date = form.joining_date.data
            employee.status = form.status.data

            try:
                db_session.commit()
                flash(f"Employee '{employee.full_name}' details updated successfully.", "success")
                return redirect(url_for("employee_detail", id=employee.id))
            except Exception as e:
                db_session.rollback()
                app.logger.error(f"Failed to update employee: {e}")
                flash("An error occurred while updating the employee record. Please try again.", "danger")

        return render_template(
            "employee_form.html",
            form=form,
            employee=employee,
            action="edit",
            page_title=f"Edit Employee: {employee.full_name}",
        )

    @app.route("/employees/<int:id>/delete", methods=["POST"])
    def employee_delete(id):
        """Deletes an employee record via POST request with CSRF protection."""
        employee = db_session.get(Employee, id)
        if not employee:
            abort(404)

        employee_name = employee.full_name
        try:
            db_session.delete(employee)
            db_session.commit()
            flash(f"Employee record for '{employee_name}' has been successfully deleted.", "info")
            return redirect(url_for("employee_list"))
        except Exception as e:
            db_session.rollback()
            app.logger.error(f"Failed to delete employee: {e}")
            flash("Could not delete employee record due to a database error.", "danger")
            return redirect(url_for("employee_detail", id=id))

    return app


# Create default application instance
app = create_app(Config)

if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5000))
    # Parse --port argument if passed by environment runners
    import sys
    for i, arg in enumerate(sys.argv):
        if arg == "--port" and i + 1 < len(sys.argv):
            try:
                port = int(sys.argv[i + 1])
            except ValueError:
                pass
    debug = os.getenv("FLASK_DEBUG", "0") in ("1", "true", "True")
    print(f"Starting TechNova Employee Management System on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
