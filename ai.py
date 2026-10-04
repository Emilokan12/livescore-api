from google import genai

MODEL = "gemini-3.5-flash-lite"  


def generate_analysis(prompt):
    # The client reads GEMINI_API_KEY from the environment
    client = genai.Client()
    response = client.models.generate_content(model=MODEL, contents=prompt)
    return response.text


def format_results(team, rows):
    if not rows:
        return f"{team}: no recent results saved yet."

    lines = [f"{team} recent results:"]
    for row in rows:
        lines.append(f"- {row.game_date}: {row.home} {row.home_score} - {row.away_score} {row.away}")
    return "\n".join(lines)


def build_prompt(game, home_recent, away_recent, live_data=None):
    return (
        "You are a sports commentator. Using ONLY the data below, write a short "
        "match preview in at most 120 words. Do not invent statistics, injuries, "
        "lineups or standings. If a team has no recent results, say there is not "
        "enough data. Do not give betting tips and do not predict an exact score.\n\n"
        f"Match: {game.home} vs {game.away} "
        f"({game.league or 'unknown league'}, {game.country or 'unknown country'}) "
        f"on {game.game_date}\n\n"
        f"{format_results(game.home, home_recent)}\n\n"
        f"{format_results(game.away, away_recent)}"
    )