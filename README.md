# TechNova Employee Management System (EMS)
### AWS RDS MySQL to Amazon Aurora MySQL Database Migration Reference

An enterprise-grade Employee Management System built to demonstrate zero-data-loss database migration workflows from **Amazon RDS for MySQL** to **Amazon Aurora MySQL**.

---

## 1. Project Overview

The **TechNova Employee Management System** provides organizational workforce management with complete CRUD operations, department analytics, searchable employee directories, and real-time database connection diagnostics.

The core engineering objective is demonstrating application compatibility across database engines—transitioning smoothly between local development (SQLite), standard relational cloud hosting (Amazon RDS for MySQL 8.x), and high-availability enterprise clustering (Amazon Aurora MySQL) strictly via configuration changes, **without code modifications**.

---

## 2. Cloud Architecture

### Architecture Before Migration (Baseline)
```
[ Client Web Browser ]
         │ (HTTPS / HTTP)
         ▼
[ EC2 Application Server ]  (Ubuntu Linux + Flask + Gunicorn)
         │ (TCP 3306 - MySQL Dialect)
         ▼
[ Amazon RDS for MySQL 8.x ] (Single-AZ or Multi-AZ Standby)
   Endpoint: technova-db.c9akxxxxxx.us-east-1.rds.amazonaws.com
```

### Architecture After Migration (Target State)
```
[ Client Web Browser ]
         │ (HTTPS / HTTP)
         ▼
[ EC2 Application Server ]  (Ubuntu Linux + Flask + Gunicorn)
         │ (TCP 3306 - MySQL Dialect)
         ▼
[ Amazon Aurora MySQL Cluster ]
   ├── Primary Writer: technova-aurora.cluster-c9akxxxxxx.us-east-1.rds.amazonaws.com
   ├── Read Replica:   technova-aurora.cluster-ro-c9akxxxxxx.us-east-1.rds.amazonaws.com
   └── Distributed 6-way replicated storage volume across 3 AZs
```

---

## 3. Technology Stack

- **Backend Framework:** Python 3.10+ / Flask 3.x
- **ORM & Dialect:** SQLAlchemy 2.x (with connection pooling and pre-ping liveness)
- **Database Driver:** PyMySQL (pure-Python MySQL 8-compatible driver)
- **Security & Forms:** Flask-WTF / WTForms with CSRF tokens & validation
- **Frontend UI:** HTML5, CSS3, Jinja2 Templates, Bootstrap 5.3 (via CDN), Bootstrap Icons
- **Supported Databases:**
  - **Local Development:** SQLite 3 (file or in-memory)
  - **AWS Cloud Production:** Amazon RDS for MySQL & Amazon Aurora MySQL
- **Test Suite:** pytest with in-memory SQLite isolation

---

## 4. Project Directory Structure

```
technova-employee-management/
├── app.py                  # Main Flask application, routes, and error handlers
├── config.py               # Environment configuration and safe connection parsing
├── database.py             # SQLAlchemy 2.x engine, scoped sessions, and health probe
├── models.py               # Employee model and index definitions
├── forms.py                # Server-side validation, duplicate email detection, CSRF
├── seed_data.py            # Non-destructive demonstration data seeder
├── requirements.txt        # Pinned Python package dependencies
├── pytest.ini              # Pytest configuration and discovery settings
├── .env.example            # Environment configuration template
├── .gitignore              # Git ignore rules for venv, secrets, and SQLite files
├── README.md               # Complete architecture and operations documentation
├── templates/
│   ├── base.html           # Master layout with sidebar, navbar, and delete modal
│   ├── dashboard.html      # KPI metrics, department stats, recent employees
│   ├── employees.html      # Paginated directory, keyword search, filters
│   ├── employee_detail.html# Full employee profile card and database metadata
│   ├── employee_form.html  # Create / Edit employee form with inline validation
│   ├── database_status.html# Connection health, engine diagnostics, latency probe
│   ├── migration_info.html # 7-Phase migration guide and verification checklist
│   ├── 404.html            # Custom not-found error template
│   └── 500.html            # Custom internal server error template
├── static/
│   ├── css/
│   │   └── style.css       # Enterprise navy/slate color palette and card styling
│   └── js/
│       └── app.js          # Mobile navigation toggle, modal hooks, health probe
└── tests/
    ├── conftest.py         # Pytest fixtures and in-memory database configuration
    ├── test_app.py         # Dashboard, status, 404, and CSRF protection tests
    ├── test_employees.py   # Full CRUD, duplicate email, search, pagination tests
    └── test_health.py      # Health endpoint (/health) and failure handling tests
```

---

## 5. Local Installation & Setup

### Prerequisites
- Python 3.10 or newer
- Git

### Step 1: Clone or Open Workspace
```bash
git clone <repository-url>
cd technova-employee-management
```

### Step 2: Create and Activate Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```
*(On Windows PowerShell: `.\.venv\Scripts\Activate.ps1`)*

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy the template configuration file:
```bash
cp .env.example .env
```
Generate a secure secret key:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```
Edit `.env` and set:
```ini
FLASK_ENV=development
SECRET_KEY=your-generated-hex-key-here
DATABASE_MODE=sqlite
```

### Step 5: Initialize and Seed Local Database
```bash
# Safely initialize tables
flask init-db

# (Optional) Seed realistic demonstration employees
python3 seed_data.py
```

### Step 6: Run Application
```bash
python3 app.py
```
Open your browser to: **`http://localhost:5000`**

---

## 6. Configuring for AWS (RDS vs Aurora)

The application detects and binds to databases exclusively through environment variables. **No source code changes are required.**

### Connecting to Amazon RDS for MySQL
Edit `.env` on your EC2 instance:
```ini
DATABASE_MODE=mysql
MYSQL_HOST=technova-db.c9akxxxxxx.us-east-1.rds.amazonaws.com
MYSQL_PORT=3306
MYSQL_DATABASE=technova_employees
MYSQL_USER=admin
MYSQL_PASSWORD=YourSecureRDSPassword
MYSQL_CONNECT_TIMEOUT=5
```

### Connecting to Amazon Aurora MySQL
Edit `.env` on your EC2 instance:
```ini
DATABASE_MODE=mysql
MYSQL_HOST=technova-aurora-cluster.cluster-c9akxxxxxx.us-east-1.rds.amazonaws.com
MYSQL_PORT=3306
MYSQL_DATABASE=technova_employees
MYSQL_USER=admin
MYSQL_PASSWORD=YourSecureAuroraPassword
MYSQL_CONNECT_TIMEOUT=5
```

Restart the application service:
```bash
sudo systemctl restart technova-ems
```

---

## 7. Migration vs. Cutover: Critical Concept

> **CRITICAL ARCHITECTURAL DISTINCTION:**
> Changing `MYSQL_HOST` in `.env` tells the application where to direct network traffic; **it does NOT copy or migrate your data**.

A true migration follows a 7-phase operational lifecycle:

1. **Phase 1: Baseline Verification** &mdash; Source RDS MySQL instance is verified with row count snapshot.
2. **Phase 2: Target Cluster Provisioning** &mdash; Aurora MySQL cluster is provisioned with matching VPC and parameters.
3. **Phase 3: Data Migration** &mdash; Data is replicated via an **Aurora Read Replica** of the RDS instance (recommended for minimum downtime) or via **AWS Database Migration Service (DMS)** / `mysqldump`.
4. **Phase 4: Target Validation** &mdash; Schema constraints, index parity, and row counts are confirmed between RDS and Aurora.
5. **Phase 5: Application Cutover** &mdash; Brief maintenance window where `MYSQL_HOST` is updated to the Aurora cluster endpoint.
6. **Phase 6: Functional Smoke Testing** &mdash; The `/health` probe and employee CRUD are verified on Aurora.
7. **Phase 7: Rollback Standby** &mdash; Source RDS MySQL instance is retained until full business sign-off before decommissioning.

---

## 8. Migration Verification Checklist

Execute these queries on both source RDS and destination Aurora:

| Verification Check | SQL / Command | Acceptance Criteria |
| :--- | :--- | :--- |
| **Row Count Parity** | `SELECT COUNT(*) FROM employees;` | Exact match between source & destination |
| **Duplicate Check** | `SELECT email, COUNT(*) FROM employees GROUP BY email HAVING COUNT(*) > 1;` | Exactly 0 records |
| **Department Parity** | `SELECT department, COUNT(*) FROM employees GROUP BY department;` | Exact match across all departments |
| **Auto-Increment State** | `SELECT AUTO_INCREMENT FROM information_schema.TABLES WHERE TABLE_NAME='employees';` | Aurora counter >= max(id) |
| **Connectivity Probe** | `curl -f http://localhost:5000/health` | HTTP 200 `{"status": "UP", ...}` |
| **Read / Write Test** | Insert and delete a verification employee | Clean write without integrity violations |

---

## 9. Automated Testing

The project includes an isolated automated test suite using in-memory SQLite (`sqlite:///:memory:`) and `StaticPool`:

```bash
pytest -v
```

All 20 tests execute without external dependencies, network access, or AWS credentials:
- Root redirect and dashboard rendering
- Employee CRUD (Create, Read, Update, Delete via POST)
- Email format validation and duplicate rejection
- Search keyword matching and multi-attribute filters
- Pagination calculations
- Custom 404 and 500 error handlers
- CSRF protection rejection on unauthenticated POSTs
- `/health` connectivity probe reporting HTTP 200 on healthy database
- Safe connectivity failure handling (HTTP 503) without credential leakage

---

## 10. Security & Production Considerations

- **Credential Hygiene:** Database passwords and full connection URIs are **never** logged to disk, rendered in HTML templates, or exposed via the JSON `/health` endpoint.
- **SQL Injection Prevention:** All queries utilize SQLAlchemy parameterization. Untrusted user inputs are never concatenated into raw SQL strings.
- **CSRF Defense:** State-changing requests (employee creation, modification, deletion) require valid CSRF tokens. Deletions are strictly restricted to `POST` methods.
- **Production Warning:** This demonstration application does not include user authentication (SSO / IAM). Before deploying to an internet-facing production environment, implement HTTPS (TLS) termination via an AWS Application Load Balancer (ALB), AWS Secrets Manager for database credentials, and AWS Cognito or corporate SSO.

---

## 11. GitHub Repository Upload

To push this codebase to your GitHub account:

```bash
# Initialize git repository if needed
git init

# Add all files (respects .gitignore)
git add .

# Commit
git commit -m "feat: complete TechNova employee management system for AWS RDS to Aurora migration"

# Set main branch and remote
git branch -M main
git remote add origin https://github.com/<your-username>/technova-employee-management.git

# Push to GitHub
git push -u origin main
```
