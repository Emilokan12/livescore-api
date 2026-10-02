from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from scraper import LiveScoreScraper
from repository import GameRepository
from routes import games
from datetime import datetime, timedelta



scraper = LiveScoreScraper()
repository = GameRepository()

def update_games(days_ahead=0):
    for sport in ["soccer", "basketball"]:
        for offset in range(days_ahead + 1):
            day = datetime.now().date() + timedelta(days=offset)
            try:
                game_list = scraper.cache_results(sport, day)
                repository.save_games(sport, game_list)
            except Exception as e:
                print(f"Error updating {sport} games for {day}: {e}")
        try:
            game_list = scraper.fetch_games(sport)
            repository.save_games(sport, game_list)
        except Exception as e:
            print(f"Error updating {sport} games: {e}")
   

scheduler = BackgroundScheduler()
scheduler.add_job(update_games, "interval", seconds=60, args=[0])
scheduler.add_job(update_games, "interval", hours=3, args=[7])