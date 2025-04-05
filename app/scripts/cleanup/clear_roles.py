"""Script to clear all roles from the database."""
import logging
import sys

import pymssql
from sqlalchemy import create_engine, text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Database connection parameters
DB_HOST = "localhost"
DB_PORT = 1433
DB_USER = "sa"
DB_PASSWORD = "YourStrong@Passw0rd"
DB_NAME = "fastapi"
DB_URL = f"mssql+pymssql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def clear_roles():
    """Clear all roles from the database."""
    # Create engine
    engine = create_engine(DB_URL, echo=True)
    
    try:
        # Create connection
        with engine.begin() as conn:
            # Delete all roles
            logger.info("Deleting all roles from the database...")
            conn.execute(text("DELETE FROM roles"))
            logger.info("All roles deleted successfully.")
    except Exception as e:
        logger.error(f"Error deleting roles: {e}")
    finally:
        # Close engine
        engine.dispose()


if __name__ == "__main__":
    clear_roles()
