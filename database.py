"""
TechNova Employee Management System — Database Layer
Provides SQLAlchemy engine, session management, table creation,
and robust connectivity health checks.
"""

import time
from datetime import datetime, timezone
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
from config import Config

Base = declarative_base()

# Global scoped session proxy initialized once
_session_factory = sessionmaker(autocommit=False, autoflush=False)
db_session = scoped_session(_session_factory)

# Attach db_session to Base for query property helper
Base.query = db_session.query_property()

engine = None


def create_app_engine(config_class=Config):
    """
    Creates and configures the SQLAlchemy engine based on configuration.
    Sets connection pooling and pre-ping to handle stale AWS connections gracefully.
    For in-memory tests, uses StaticPool so the in-memory database is shared across threads/requests.
    """
    db_uri = config_class.get_database_uri()

    engine_kwargs = {
        "future": True,
    }

    if config_class.DATABASE_MODE == "mysql":
        engine_kwargs.update({
            "pool_size": config_class.DB_POOL_SIZE,
            "max_overflow": config_class.DB_MAX_OVERFLOW,
            "pool_recycle": config_class.DB_POOL_RECYCLE,
            "pool_timeout": config_class.DB_POOL_TIMEOUT,
            "pool_pre_ping": True,  # Verifies connection liveness before checkout
        })
    elif "sqlite" in db_uri:
        if ":memory:" in db_uri or db_uri == "sqlite://":
            engine_kwargs.update({
                "connect_args": {"check_same_thread": False},
                "poolclass": StaticPool,
            })
        else:
            engine_kwargs["connect_args"] = {"check_same_thread": False}

    return create_engine(db_uri, **engine_kwargs)


def init_app_db(app, config_class=Config):
    """
    Initializes database engine, configures scoped session, and registers teardown hook with Flask app.
    Safely creates tables if they do not exist, without dropping or erasing existing data.
    """
    global engine

    engine = create_app_engine(config_class)
    # Configure the global scoped session with the active engine
    db_session.configure(bind=engine)

    # Safely create tables if they don't already exist (non-destructive)
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        app.logger.warning(f"Database initialization warning: Table check skipped or failed: {e.__class__.__name__}")

    # Register session cleanup hook after each request
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

    return engine, db_session


def check_db_connectivity(config_class=Config) -> dict:
    """
    Performs a lightweight, read-only connectivity check against the active database.
    Returns structured health metadata. Never exposes sensitive passwords or full URLs.
    """
    start_time = time.time()
    safe_info = config_class.get_safe_db_info()
    timestamp_iso = datetime.now(timezone.utc).isoformat()

    global engine
    active_engine = engine

    # Fallback if engine is not yet created
    if active_engine is None:
        try:
            active_engine = create_app_engine(config_class)
        except Exception as e:
            return {
                "connected": False,
                "error": f"Failed to initialize engine: {e.__class__.__name__}",
                "latency_ms": None,
                "checked_at": timestamp_iso,
                **safe_info,
            }

    try:
        with active_engine.connect() as conn:
            # Simple lightweight connectivity query
            conn.execute(text("SELECT 1"))
        latency_ms = round((time.time() - start_time) * 1000, 2)
        return {
            "connected": True,
            "error": None,
            "latency_ms": latency_ms,
            "checked_at": timestamp_iso,
            **safe_info,
        }
    except Exception as err:
        latency_ms = round((time.time() - start_time) * 1000, 2)
        # Sanitize any error message to ensure no passwords or credentials leak
        err_msg = str(err)
        if config_class.MYSQL_PASSWORD and config_class.MYSQL_PASSWORD in err_msg:
            err_msg = err_msg.replace(config_class.MYSQL_PASSWORD, "********")
        clean_error = f"{err.__class__.__name__}: {err_msg[:120]}"

        return {
            "connected": False,
            "error": clean_error,
            "latency_ms": latency_ms,
            "checked_at": timestamp_iso,
            **safe_info,
        }
