from database import SessionLocal
from models import GameRow

class GameRepository:
    def save_games(self, sport, games):
        session = SessionLocal()
        for game in games:
            existing = session.query(GameRow).filter(GameRow.event_id == game["event_id"]).first()
            if existing:
                existing.home = game["home"]
                existing.away = game["away"]
                existing.home_score = game["home_score"]
                existing.away_score = game["away_score"]
                existing.status = game["status"]
                existing.game_date = game["game_date"]
                existing.league = game["league"]
            else:
                new_game = GameRow(
                    event_id=game["event_id"],
                    sport=sport,
                    home=game["home"],
                    away=game["away"],
                    home_score=game["home_score"],
                    away_score=game["away_score"],
                    status=game["status"],
                    game_date=game["game_date"],
                    league=game["league"],
                    country=game["country"]
                )
                session.add(new_game)
        session.commit()
        session.close()

    def get_by_team(self, sport, team):   
        session = SessionLocal()
        games = session.query(GameRow).filter(GameRow.sport == sport,
                    (GameRow.home.like(f"%{team}%")) | (GameRow.away.like(f"%{team}%"))).order_by(GameRow.game_date,GameRow.start_time).all()
        session.close()
        return games