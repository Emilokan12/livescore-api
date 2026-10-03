from datetime import date

from fastapi import APIRouter, HTTPException

from ai import build_prompt, generate_analysis
from repository import GameRepository

router = APIRouter()
repository = GameRepository()

DAILY_LIMIT = 50                      
cache = {}                            
usage = {"day": date.today(), "count": 0}


@router.get("/analysis/{event_id}")
def get_analysis(event_id: str):
    if event_id in cache:
        return {"event_id": event_id, "analysis": cache[event_id], "cached": True}

    game = repository.get_game(event_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    today = date.today()
    if usage["day"] != today:
        usage["day"] = today
        usage["count"] = 0
    if usage["count"] >= DAILY_LIMIT:
        raise HTTPException(status_code=429, detail="Daily analysis limit reached, try again tomorrow")

    prompt = build_prompt(game)

    try:
        text = generate_analysis(prompt)
    except Exception as e:
        print(f"Analysis error: {e}")
        raise HTTPException(status_code=503, detail="Analysis is unavailable right now")

    if not text:
        raise HTTPException(status_code=503, detail="Analysis is unavailable right now")

    usage["count"] += 1
    cache[event_id] = text
    return {"event_id": event_id, "analysis": text, "cached": False}