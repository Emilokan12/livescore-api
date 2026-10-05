import os

from google import genai
from google.genai import types


MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
USE_SEARCH = os.environ.get("GEMINI_SEARCH") == "1"


def get_sources(response):
    """Return up to 5 (title, link) pairs for the pages Google Search used."""
    try:
        chunks = response.candidates[0].grounding_metadata.grounding_chunks or []
    except (AttributeError, IndexError, TypeError):
        return []

    sources = []
    for chunk in chunks[:5]:
        web = getattr(chunk, "web", None)
        if web is not None and getattr(web, "uri", None):
            sources.append((getattr(web, "title", None) or web.uri, web.uri))
    return sources


def generate_analysis(prompt):
    # The client reads GEMINI_API_KEY from the environment
    client = genai.Client()

    config = None
    if USE_SEARCH:
        config = types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())]
        )

    response = client.models.generate_content(
        model=MODEL, contents=prompt, config=config
    )

    text = response.text
    if not text:
        return None

    if USE_SEARCH:
        sources = get_sources(response)
        if sources:
            text += "\n\n**Sources**\n" + "\n".join(f"- [{t}]({u})" for t, u in sources)
    return text


def format_results(team, rows):
    if not rows:
        return f"{team}: no recent results saved."

    lines = [f"{team} last results (newest first):"]
    for row in rows:
        lines.append(f"- {row.game_date}: {row.home} {row.home_score} - {row.away_score} {row.away}")
    return "\n".join(lines)


def build_prompt(game, home_recent, away_recent, live_data=None):
    is_soccer = game.sport == "soccer"
    outcomes = "home win / draw / away win" if is_soccer else "home win / away win"
    markets = (
        "result, double chance, total goals over/under, both teams to score"
        if is_soccer
        else "moneyline, point spread, total points over/under"
    )

    if USE_SEARCH:
        knowledge = (
            "Also use Google Search to find current form, injuries, suspensions and "
            "likely lineups. Only state facts you found.\n"
        )
    else:
        knowledge = (
            "For everything else, use your general knowledge of both teams. Your "
            "knowledge may be out of date, so say clearly when you are unsure.\n"
        )

    if live_data:
        live_block = (
            "Current data from football-data.org. This is the most reliable and "
            "up-to-date information you have, so use it first and quote the numbers "
            "exactly as given:\n"
            f"{live_data}\n\n"
        )
        saved_label = "Other results saved in our own database (use these second):"
    else:
        live_block = ""
        saved_label = (
            "Recent results saved in our database. These are the most current data "
            "you have, so use them first:"
        )

    return (
        f"You are a {game.sport} analyst. Write a detailed match preview for:\n\n"
        f"{game.home} vs {game.away} "
        f"({game.league or 'unknown league'}, {game.country or 'unknown country'}) "
        f"on {game.game_date}\n\n"
        f"{live_block}"
        f"{saved_label}\n"
        f"{format_results(game.home, home_recent)}\n"
        f"{format_results(game.away, away_recent)}\n\n"
        f"{knowledge}\n"
        "Use exactly these markdown headings:\n"
        "## Overview\n"
        "## Form and key factors\n"
        "## Likely outcome\n"
        "## H2H Record\n"
        f"Give the last five match the teams have played together"
        f"Say who is more likely to win and give rough percentages for: {outcomes}. "
        "State your confidence as low, medium or high.\n"
        "## Betting angles\n"
        f"Give 2 or 3 ideas from these markets: {markets}. For each, give a short "
        "reason and a risk level (low, medium or high).\n"
        "## Check before betting\n"
        "List what you cannot see: injuries, suspensions, lineups and the latest odds.\n\n"
        "Rules:\n"
        "- This is an estimate. Never call a bet guaranteed or a sure thing.\n"
        "- Do not invent statistics, injuries or lineups.\n"
        "- If you do not know a team well, say so and lower your confidence.\n"
        "- Do not suggest stake sizes.\n"
        "- Keep it under 350 words."
    )