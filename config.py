"""
TechNova Employee Management System — Configuration Module
Handles environment variables, database selection, connection strings,
and security settings for both development and testing.
"""

import os
from pathlib import Path
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


class Config:
    """Base application configuration."""

    SECRET_KEY = os.getenv("SECRET_KEY", "technova-default-dev-secret-key-change-in-prod-32bytes")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = os.getenv("FLASK_DEBUG", "0") in ("1", "true", "True")
    TESTING = False

    # CSRF Protection enabled by default
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600

    # Database Selection: 'sqlite' or 'mysql'
    DATABASE_MODE = os.getenv("DATABASE_MODE", "sqlite").strip().lower()

    # MySQL Configuration (Amazon RDS for MySQL or Amazon Aurora MySQL)
    MYSQL_HOST = os.getenv("MYSQL_HOST", "").strip()
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "technova_employees").strip()
    MYSQL_USER = os.getenv("MYSQL_USER", "").strip()
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "").strip()
    MYSQL_CONNECT_TIMEOUT = int(os.getenv("MYSQL_CONNECT_TIMEOUT", "5"))

    # Connection pool configuration for MySQL
    DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
    DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "1800"))
    DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))

    # SQLite Configuration
    SQLITE_DB_NAME = os.getenv("SQLITE_DB_PATH", "instance_data/technova_employees.db").strip()

    @classmethod
    def get_database_uri(cls) -> str:
        """
        Constructs the SQLAlchemy database URI based on DATABASE_MODE.
        Safely formats MySQL connection string with URL encoding for credentials.
        """
        if cls.DATABASE_MODE == "mysql":
            user = quote_plus(cls.MYSQL_USER)
            password = quote_plus(cls.MYSQL_PASSWORD)
            host = cls.MYSQL_HOST
            port = cls.MYSQL_PORT
            database = cls.MYSQL_DATABASE
            timeout = cls.MYSQL_CONNECT_TIMEOUT
            return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?connect_timeout={timeout}"

        # Default: SQLite
        instance_dir = BASE_DIR / "instance_data"
        instance_dir.mkdir(parents=True, exist_ok=True)
        sqlite_file = BASE_DIR / cls.SQLITE_DB_NAME
        sqlite_file.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{sqlite_file}"

    @classmethod
    def get_safe_db_info(cls) -> dict:
        """
        Returns safe database configuration metadata for display and health checks.
        NEVER returns raw passwords or full connection URLs containing credentials.
        """
        if cls.DATABASE_MODE == "mysql":
            masked_host = cls.MYSQL_HOST if cls.MYSQL_HOST else "(not configured)"
            return {
                "mode": "mysql",
                "engine_type": "Amazon RDS / Aurora MySQL Compatible",
                "dialect": "mysql+pymysql",
                "host": masked_host,
                "port": cls.MYSQL_PORT,
                "database_name": cls.MYSQL_DATABASE or "(not configured)",
                "user": cls.MYSQL_USER or "(not configured)",
                "connect_timeout_seconds": cls.MYSQL_CONNECT_TIMEOUT,
            }
        return {
            "mode": "sqlite",
            "engine_type": "SQLite (Local File)",
            "dialect": "sqlite",
            "host": "localhost (local file)",
            "port": "N/A",
            "database_name": cls.SQLITE_DB_NAME,
            "user": "N/A",
            "connect_timeout_seconds": "N/A",
        }


class TestConfig(Config):
    """Configuration for automated test execution using in-memory SQLite."""

    TESTING = True
    DEBUG = False
    WTF_CSRF_ENABLED = False  # Allows form testing without CSRF token generation in unit tests
    DATABASE_MODE = "sqlite"

    @classmethod
    def get_database_uri(cls) -> str:
        return "sqlite:///:memory:"

    @classmethod
    def get_safe_db_info(cls) -> dict:
        return {
            "mode": "sqlite",
            "engine_type": "SQLite (In-Memory)",
            "dialect": "sqlite",
            "host": "in-memory",
            "port": "N/A",
            "database_name": ":memory:",
            "user": "test_runner",
            "connect_timeout_seconds": "N/A",
        }
