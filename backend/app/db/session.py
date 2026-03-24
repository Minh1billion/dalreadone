from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import Config

engine = create_engine(Config.SQL_CONNECTION_STRING)

SessionLocal = sessionmaker(bind=engine)

# DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()