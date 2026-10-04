import html
from datetime import datetime
from urllib.parse import quote
from zoneinfo import ZoneInfo

import requests
import streamlit as st

# Your Render address (no slash at the end)
API_URL = "https://livescore-api-kpad.onrender.com"
LOCAL_TZ = ZoneInfo("Africa/Lagos")
FINISHED = {"FT", "AET", "AP"}

st.set_page_config(page_title="Live Scores", page_icon="🏀")

st.markdown(
    """
<style>
.league {font-weight:700; font-size:0.9rem; padding:8px 12px; margin-top:16px;
         background:rgba(128,128,128,0.15); border-radius:8px 8px 0 0;}
.row {display:grid; grid-template-columns:78px 1fr 60px 1fr; align-items:center;
      gap:6px; padding:10px 12px; border-bottom:1px solid rgba(128,128,128,0.2);}
.status {font-size:0.8rem; opacity:0.7;}
.status.live {color:#e53935; font-weight:700; opacity:1;}
.team {font-size:0.95rem;}
.team.home {text-align:right;}
.score {text-align:center; font-weight:700; border-radius:6px; padding:2px 0;
        background:rgba(128,128,128,0.15);}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data(ttl=20)
def load_games(sport, team, day_text):
    if team:
        url = f"{API_URL}/games/{sport}/team/{quote(team)}"
        params = {}
    else:
        url = f"{API_URL}/games/{sport}"
        params = {"day": day_text} if day_text else {}

    response = requests.get(url, params=params, timeout=60)
    if response.status_code == 404:
        return []
    response.raise_for_status()
    return response.json()


def to_local(iso_text):
    if not iso_text:
        return None
    return datetime.fromisoformat(iso_text).astimezone(LOCAL_TZ)


def status_label(game, show_date):
    status = game.get("status") or ""
    if status == "NS":
        local = to_local(game.get("start_time"))
        if local is None:
            return "NS", ""
        fmt = "%d %b %H:%M" if show_date else "%H:%M"
        return local.strftime(fmt), ""
    if status in FINISHED:
        return status, ""
    return status, "live"  # HT, 45', and so on


def render(games, show_date):
    leagues = {}
    for game in games:
        key = (game.get("country") or "", game.get("league") or "Other")
        leagues.setdefault(key, []).append(game)

    parts = []
    for (country, league), items in leagues.items():
        title = f"{country} · {league}" if country else league
        parts.append(f'<div class="league">{html.escape(title)}</div>')

        for game in sorted(items, key=lambda g: g.get("start_time") or ""):
            label, css = status_label(game, show_date)
            if game["home_score"] is None or game["away_score"] is None:
                score = "-"
            else:
                score = f"{game['home_score']} - {game['away_score']}"

            parts.append(
                f'<div class="row">'
                f'<div class="status {css}">{html.escape(label)}</div>'
                f'<div class="team home">{html.escape(game["home"])}</div>'
                f'<div class="score">{score}</div>'
                f'<div class="team away">{html.escape(game["away"])}</div>'
                f"</div>"
            )

    st.markdown("".join(parts), unsafe_allow_html=True)


st.title("Live Scores")

if "page" not in st.session_state:
    st.session_state.page = "scores"


@st.fragment(run_every=30)
def show_games(sport, team, day_text):
    try:
        games = load_games(sport, team, day_text)
    except requests.RequestException:
        st.error("Could not reach the API. It may be waking up, so try again in a minute.")
        return

    if not games:
        st.info("No games found.")
    else:
        st.caption(f"{len(games)} games")
        render(games, show_date=bool(team))


def scores_page():
    sport = st.selectbox("Sport", ["soccer", "basketball"], key="scores_sport")
    col1, col2 = st.columns(2)
    team = col1.text_input(
        "Search a team", help="Shows all saved games for that team", key="scores_team"
    )
    day = col2.date_input(
        "Date",
        value=None,
        format="YYYY-MM-DD",
        help="Leave empty for today. Ignored when a team is typed.",
        key="scores_day",
    )

    btn1, btn2 = st.columns(2)
    if btn1.button("Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    if btn2.button("Analysis", use_container_width=True):
        st.session_state.page = "analysis"
        st.rerun()

    show_games(sport, team.strip(), day.isoformat() if day else "")


def analysis_page():
    if st.button("← Back to scores"):
        st.session_state.page = "scores"
        st.rerun()

    st.subheader("Match analysis")
    sport = st.selectbox("Sport", ["soccer", "basketball"], key="analysis_sport")
    team = st.text_input("Search a team to analyse", key="analysis_team").strip()

    if not team:
        st.info("Type a team name to find its games.")
        return

    try:
        games = load_games(sport, team, "")
    except requests.RequestException:
        st.error("Could not load the games. Try again in a minute.")
        return
    if not games:
        st.info("No saved games found for that team.")
        return

    options = {
        f"{g.get('game_date', '')} · {g['home']} vs {g['away']}": g["event_id"]
        for g in games
    }
    choice = st.selectbox("Pick a game", list(options.keys()))

    if st.button("Analyse"):
        with st.spinner("Analysing..."):
            try:
                response = requests.get(f"{API_URL}/analysis/{options[choice]}", timeout=60)
            except requests.RequestException:
                st.error("Could not reach the API. Try again in a minute.")
                return

        if response.ok:
            st.write(response.json()["analysis"])
            st.caption("AI-generated. It can make mistakes and may be out of date. Not betting advice.")
        elif response.status_code == 429:
            st.warning("The daily analysis limit has been reached. Try again tomorrow.")
        else:
            st.error("Analysis is unavailable right now.")


if st.session_state.page == "analysis":
    analysis_page()
else:
    scores_page()
