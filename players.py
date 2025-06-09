from sqlmodel import SQLModel, Field, create_engine, Session
from sqlalchemy import inspect

# Database URL for players
player_db_url = "sqlite:///players.db"
player_engine = create_engine(player_db_url)

# Player Table Definition
class Player(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str

# Create table if it doesn't exist
inspector = inspect(player_engine)
if "player" not in inspector.get_table_names():
    SQLModel.metadata.create_all(player_engine)

# Session helper
def get_player_session():
    return Session(player_engine)

# Helper functions
def get_players():
    with get_player_session() as session:
        return [p.name for p in session.query(Player).all()]

def add_player(name: str):
    with get_player_session() as session:
        player = Player(name=name)
        session.add(player)
        session.commit()

def remove_player(name: str):
    with get_player_session() as session:
        player = session.query(Player).filter(Player.name == name).first()
        if player:
            session.delete(player)
            session.commit()

