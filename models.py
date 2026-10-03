from pydantic import BaseModel, ConfigDict
from sqlalchemy import String, Integer, or_
from sqlalchemy.orm import Mapped, mapped_column
from database import Base, engine

class Game(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    event_id: str | None = None
    home: str
    away: str
    home_score: int | None = None
    away_score: int | None = None
    status: str | None = None
    game_date: str | None = None
    league: str | None = None
    country: str | None = None
    start_time: str | None = None


class GameRow(Base):
    __tablename__ = "games_v3"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[str] = mapped_column(String(50), unique=True)
    sport: Mapped[str] = mapped_column(String(50))
    home: Mapped[str] = mapped_column(String(100))
    away: Mapped[str] = mapped_column(String(100))
    home_score: Mapped[int | None] = mapped_column(Integer, nullable=True) 
    away_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(50))
    game_date: Mapped[str] = mapped_column(String(10)) 
    league: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    start_time: Mapped[str | None] = mapped_column(String(40), nullable=True)

Base.metadata.create_all(engine)