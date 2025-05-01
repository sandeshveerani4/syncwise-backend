from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,declarative_base
import os

engine = create_engine(os.environ.get('DATABASE_URI'),pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
