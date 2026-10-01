from scraper import LiveScoreScraper
from fastapi import APIRouter, HTTPException
import requests
from models import Game
import fastapi
from repository import GameRepository

router = APIRouter()
scraper = LiveScoreScraper()
repository = GameRepository()

@router.get("/games/{sport}", response_model=list[Game])
def get_games(sport: str, status: str | None = None):
    try:
        games = scraper.cache_results(sport)
        repository.save_games(sport, games)
        if status:
            games = [game for game in games if game["status"] == status]
        return games
    except requests.HTTPError:
        raise fastapi.HTTPException(status_code=404, detail="Sport not found")

@router.get("/games/{sport}/team/{team}", response_model=list[Game])
def get_by_team(sport: str, team: str):
    games = repository.get_by_team(sport, team)
    if not games:
        raise fastapi.HTTPException(status_code=404, detail="No games found for the specified team")
    return [Game(event_id=game.event_id, home=game.home, away=game.away, home_score=game.home_score, away_score=game.away_score, status=game.status) for game in games]