from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from scraper import LiveScoreScraper
from repository import GameRepository
from routes import games
from datetime import datetime



scraper = LiveScoreScraper()
repository = GameRepository()

def update_games():
    for sport in ["soccer"]:
        try:
            game_list = scraper.fetch_games(sport)
            repository.save_games(sport, game_list)
        except Exception as e:
            print(f"Error updating {sport} games: {e}")
   

scheduler = BackgroundScheduler()
scheduler.add_job(update_games, "interval", seconds=60, next_run_time=datetime.now())

