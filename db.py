from sqlmodel import SQLModel, create_engine, Session
from models import Player, Team, Match

sqlite_url = "sqlite:///volleyball.db"
engine = create_engine(sqlite_url, echo=False)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    return Session(engine)
