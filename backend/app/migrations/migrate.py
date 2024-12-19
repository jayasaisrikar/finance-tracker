from sqlalchemy import create_engine
from app.database import SQLALCHEMY_DATABASE_URL
from app.models import Base

def migrate():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    migrate() 