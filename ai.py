import os

from google import genai
from google.genai import types

# Both can be changed on Render (Environment) without touching the code:
#   GEMINI_MODEL  - the model name
#   GEMINI_SEARCH - set to 1 to let the AI search Google (needs a plan that allows it)
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


def build_prompt(game):
    intro = (
        f"You are a {game.sport} analyst. Write a short match preview in at most "
        "180 words for this game:\n\n"
        f"{game.home} vs {game.away} "
        f"({game.league or 'unknown league'}, {game.country or 'unknown country'}) "
        f"on {game.game_date}\n\n"
    )

    if USE_SEARCH:
        source_rules = (
            "Use Google Search to find current information about both teams: recent "
            "results, current form, injuries, suspensions and likely lineups.\n\n"
            "Rules:\n"
            "- Only state facts you found. If you cannot find something, say so.\n"
        )
    else:
        source_rules = (
            "Use your general knowledge of both teams: their playing style, strengths, "
            "weaknesses and how the clubs have generally performed.\n\n"
            "Rules:\n"
            "- Your knowledge may be out of date. Do not claim to know current form, "
            "injuries, suspensions, lineups or recent results. Say these should be checked.\n"
        )

    return (
        intro
        + source_rules
        + "- If you cannot identify a team, say so instead of guessing.\n"
        "- Do not invent statistics.\n"
        "- Do not give betting tips and do not predict an exact score."
    )
