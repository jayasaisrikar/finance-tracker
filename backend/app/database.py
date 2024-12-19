from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the directory containing this file
current_dir = Path(__file__).resolve().parent
env_path = current_dir / '.env'

# Load environment variables from the correct path
load_dotenv(dotenv_path=env_path)

# Log environment variable status
env_vars = ['POSTGRES_USER', 'POSTGRES_PASSWORD', 'POSTGRES_HOST', 'POSTGRES_DATABASE']
for var in env_vars:
    logger.info(f"{var} is {'set' if os.getenv(var) else 'not set'}")

# Construct Database URL with error handling
db_params = {
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'host': os.getenv('POSTGRES_HOST'),
    'database': os.getenv('POSTGRES_DATABASE')
}

# Validate required parameters
missing_vars = [key for key, value in db_params.items() if not value]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars).upper()}")

SQLALCHEMY_DATABASE_URL = f"postgresql://{db_params['user']}:{db_params['password']}@{db_params['host']}:5432/{db_params['database']}?sslmode=require"

try:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        connect_args={"sslmode": "require"}
    )
    # Test the connection using SQLAlchemy text()
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
        logger.info("Database connection successful!")
except Exception as e:
    logger.error(f"Database connection error: {str(e)}")
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

