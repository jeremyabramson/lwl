from sqlmodel import SQLModel, Field, create_engine, Session
from datetime import date
from sqlalchemy import inspect

# Database URL
db_url = "sqlite:///volleyball_matches.db"
engine = create_engine(db_url)

# Match Table Definition
class Match(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}

    id: int = Field(default=None, primary_key=True)
    player1: str
    player2: str
    player3: str
    player4: str
    score1_2: int
    score3_4: int
    location: str
    date: date
    time: str
    notes: str    

# Create table if it doesn't exist
inspector = inspect(engine)

if not inspect(engine).has_table("match"):
    SQLModel.metadata.create_all(engine)

# Session helper
def get_session():
    return Session(engine)

