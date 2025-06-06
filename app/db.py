
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
#  placeholder for the actual database URL
DATABASE_URL = "postgresql://username:password@localhost:5432/chatdb"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)
