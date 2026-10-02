import requests
from datetime import datetime, date

class LiveScoreScraper:
    def __init__(self):     
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebkit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.livescore.com/"
        }
        self.cache = {}

    def build_url(self, sport, day):
        url = f"https://prod-cdn-mev-api.livescore.com/api/v2/date/{sport}/{day.strftime('%Y%m%d')}/1?CountryCode=NG&paging=false&locale=en"
        return url

    def cache_results(self, sport, day=None):
        day = day or date.today()
        key = (sport, day)
        current_time = datetime.now().timestamp()
        if key in self.cache and (current_time - self.cache[key]["time"]) < 30:
            return self.cache[key]["games"]
        games = self.fetch_games(sport, day)
        self.cache[key] = {"games": games, "time": current_time}
        return games

    
    def fetch_games(self, sport, day=None):
        day = day or date.today()
        url = self.build_url(sport, day)
        response = requests.get(url, headers=self.headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        games_list = []
        for league in data["Sctns"]:
            for game in league["Ts"]["Evs"]:
                games_list.append({
                    "event_id": game["Eid"],
                    "home": game["T1"][0]["Nm"], 
                    "home_score": game.get("Tr1"), 
                    "away": game["T2"][0]["Nm"], 
                    "away_score": game.get("Tr2"), 
                    "status": game.get("Eps", "unknown"), 
                    "game_date": day.isoformat()
                })
        return games_list

from datetime import date, timedelta
scraper = LiveScoreScraper()
print(scraper.fetch_games("soccer", date.today() + timedelta(days=1))[:3])