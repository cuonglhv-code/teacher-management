"""Run Alembic migrations against production database."""
import os
import sys
from alembic.config import Config
from alembic import command


def run_migrations():
    """Run database migrations."""
    # Get database URL from environment
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL environment variable is not set")
        sys.exit(1)
    
    # Ensure SSL mode is set for Neon
    if "sslmode" not in db_url and db_url.startswith("postgresql"):
        if "?" in db_url:
            db_url += "&sslmode=require"
        else:
            db_url += "?sslmode=require"
    
    # Set the database URL for Alembic
    os.environ["DATABASE_URL"] = db_url
    
    # Run migrations
    try:
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", db_url)
        command.upgrade(alembic_cfg, "head")
        print("✓ Migrations completed successfully!")
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_migrations()