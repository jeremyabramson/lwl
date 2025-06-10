from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import date

class Player(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

class Team(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    player1_id: int = Field(foreign_key="player.id")
    player2_id: int = Field(foreign_key="player.id")

    player1: Optional["Player"] = Relationship(sa_relationship_kwargs={"foreign_keys": "[Team.player1_id]"})
    player2: Optional["Player"] = Relationship(sa_relationship_kwargs={"foreign_keys": "[Team.player2_id]"})

class Match(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    team1_id: int = Field(foreign_key="team.id")
    team2_id: int = Field(foreign_key="team.id")
    score_team1: int
    score_team2: int
    location: str
    date: date
    time: str
    notes: Optional[str] = ""

