import difflib
import os
import re
import time
import unicodedata
 
import requests
 
BASE = "https://api.football-data.org/v4"
 
# Free competitions, matched to the country name livescore uses
COMPETITIONS = {
    "PL": "England",
    "ELC": "England",
    "PD": "Spain",
    "SA": "Italy",
    "BL1": "Germany",
    "FL1": "France",
    "DED": "Netherlands",
    "PPL": "Portugal",
    "BSA": "Brazil",
}
 
_cache = {}
 
 
def cached(key, loader, ttl):
    now = time.time()
    hit = _cache.get(key)
    if hit and now - hit[0] < ttl:
        return hit[1]
    value = loader()
    if value is not None:
        _cache[key] = (now, value)
    return value
 
 
def fd_get(path, params=None):
    key = os.environ.get("FOOTBALL_DATA_KEY")
    if not key:
        return None
    response = requests.get(
        f"{BASE}{path}", headers={"X-Auth-Token": key}, params=params, timeout=10
    )
    if response.status_code != 200:
        print(f"football-data: {path} returned {response.status_code}")
        return None
    return response.json()
 
 
def normalize(name):
    name = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode().lower()
    name = re.sub(r"[^a-z0-9 ]", " ", name)
    skip = {"fc", "afc", "cf", "ac", "sc", "club", "the"}
    return " ".join(w for w in name.split() if w not in skip)
 
 
def find_team(teams, name):
    target = normalize(name)
    if not target:
        return None
 
    names = []
    for team in teams:
        for label in (team.get("name"), team.get("shortName")):
            if label:
                names.append((normalize(label), team))
 
    for label, team in names:          # exact match
        if label == target:
            return team
    for label, team in names:          # one name inside the other
        if label and (label in target or target in label):
            return team
 
    best, best_score = None, 0.85      # close spelling
    for label, team in names:
        score = difflib.SequenceMatcher(None, label, target).ratio()
        if score > best_score:
            best, best_score = team, score
    return best
 
 
def get_teams(code):
    def load():
        data = fd_get(f"/competitions/{code}/teams")
        return data.get("teams", []) if data else None
    return cached(("teams", code), load, ttl=24 * 3600)
 
 
def get_table(code):
    def load():
        data = fd_get(f"/competitions/{code}/standings")
        if not data:
            return None
        rows = {}
        for standing in data.get("standings", []):
            if standing.get("type") == "TOTAL":
                for row in standing.get("table", []):
                    rows[row["team"]["id"]] = row
        return rows
    return cached(("table", code), load, ttl=6 * 3600)
 
 
def get_last_results(team_id, limit=5):
    def load():
        data = fd_get(f"/teams/{team_id}/matches", {"status": "FINISHED"})
        return data.get("matches", []) if data else None
 
    matches = cached(("matches", team_id), load, ttl=3 * 3600) or []
    matches = sorted(matches, key=lambda m: m.get("utcDate", ""), reverse=True)
    return matches[:limit]
 
 
def result_letter(match, team_id):
    score = match.get("score", {}).get("fullTime", {})
    home, away = score.get("home"), score.get("away")
    if home is None or away is None:
        return "?"
    mine, theirs = (home, away) if match["homeTeam"]["id"] == team_id else (away, home)
    return "W" if mine > theirs else "L" if mine < theirs else "D"
 
 
def describe_team(label, team, row, matches):
    lines = [f"{label} ({team['name']}):"]
    if row:
        lines.append(
            f"- Table position {row['position']}, {row['playedGames']} played, "
            f"{row['points']} points, W{row['won']} D{row['draw']} L{row['lost']}, "
            f"goals {row['goalsFor']}-{row['goalsAgainst']}"
        )
    if matches:
        form = "".join(result_letter(m, team["id"]) for m in matches)
        lines.append(f"- Last {len(matches)} results (newest first): {form}")
        for m in matches:
            score = m["score"]["fullTime"]
            lines.append(
                f"  {m['utcDate'][:10]}: {m['homeTeam']['name']} "
                f"{score['home']}-{score['away']} {m['awayTeam']['name']}"
            )
    return "\n".join(lines)
 
 
def competitions_for(game):
    if "champions league" in (game.league or "").lower():
        return ["CL"]
    country = (game.country or "").lower()
    return [code for code, c in COMPETITIONS.items() if c.lower() == country]
 
 
def _get_context(game):
    if not os.environ.get("FOOTBALL_DATA_KEY"):
        return None
 
    for code in competitions_for(game):
        teams = get_teams(code)
        if not teams:
            continue
 
        home = find_team(teams, game.home)
        away = find_team(teams, game.away)
        if home is None and away is None:
            continue
 
        table = get_table(code) or {}
        parts = [f"Competition: {code}. Source: football-data.org, current season."]
        for label, team in (("Home team", home), ("Away team", away)):
            if team is None:
                continue
            parts.append(
                describe_team(label, team, table.get(team["id"]), get_last_results(team["id"]))
            )
        return "\n".join(parts)
 
    print(f"football-data: no match for {game.home} vs {game.away} ({game.country}, {game.league})")
    return None
 
 
def get_context(game):
    try:
        return _get_context(game)
    except Exception as e:
        print(f"football-data error: {e}")
        return None
 
