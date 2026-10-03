# Live Scores API

A REST API that scrapes live sports scores from livescore.com, cleans the data, stores it in a database, and serves it through FastAPI. A background job keeps the stored data up to date, so game history builds up even when nobody is calling the API.

## Features

- **Scraper class** that fetches the day's games for any sport and returns clean data (home, away, scores, status)
- **In-memory cache** (30 seconds per sport) so repeated requests don't hit livescore every time
- **Database storage** with SQLAlchemy. Games are saved by their livescore event ID, so a game is updated, never duplicated
- **Scheduled updates** with APScheduler, refreshing scores every 60 seconds in the background
- **Filtering** by game status, and **search** by team name (case-insensitive, partial matches work)
- **Typed responses** with Pydantic, shown automatically in the interactive docs
- **Tests** with pytest

## Endpoints

### `GET /games/{sport}`

Returns today's games for a sport. Sport names are livescore's own, for example `basketball` and `soccer`.

Optional query parameter: `status` filters by game status (`NS` = not started, `FT` = full time).

```
GET /games/basketball
GET /games/basketball?status=NS
```

Example response:

```json
[
  {
    "event_id": "1898715",
    "home": "New York Liberty",
    "away": "Minnesota Lynx",
    "home_score": 87,
    "away_score": 71,
    "status": "FT"
  }
]
```

Scores are `null` for games that haven't started. An unknown sport returns `404`.

### `GET /games/{sport}/team/{team}`

Returns saved games where the team plays at home or away. The match is partial and not case-sensitive, so `madrid` finds "Real Madrid". Returns `404` if nothing matches.

```
GET /games/basketball/team/Real Madrid
```

Interactive documentation is available at `/docs` when the app is running.

## Run it locally

```bash
git clone https://github.com/Emilokan12/livescore-api.git
cd livescore-api
pip install -r requirements.txt
uvicorn main:app --reload
```
Then open http://127.0.0.1:8000/docs.

The SQLite database file (`games.db`) is created automatically on first run. Run the commands from the project folder, because the database path is relative.

## Run the tests

```bash
python -m pytest
```

Note: one test calls the real livescore API, so it needs an internet connection.

## Project structure

```
├── main.py            # FastAPI app and scheduler startup
├── jobs.py            # Background job that refreshes and saves games
├── scraper.py         # LiveScoreScraper: fetching, cleaning, caching
├── repository.py      # GameRepository: saving and querying games
├── models.py          # Pydantic model (API) and SQLAlchemy model (database)
├── database.py        # Database engine and session setup
├── routes/
│   └── games.py       # API endpoints
├── tests/
│   └── test_api.py
└── requirements.txt
```
## Live Link
https://livescore-api-kpad.onrender.com/docs
https://livescore-api-kpad.onrender.com

## Tech

Python, FastAPI, SQLAlchemy, SQLite, APScheduler, Pydantic, requests, pytest

## Roadmap

- PostgreSQL support through a `DATABASE_URL` environment variable
- Docker and a public deployment
- Telegram alerts when a chosen team's game starts or ends
- Tests that use fake data instead of the live API
