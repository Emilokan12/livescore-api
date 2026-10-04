import html
from datetime import date, datetime, timedelta
from urllib.parse import quote
from zoneinfo import ZoneInfo

import requests
import streamlit as st

# Your Render address (no slash at the end)
API_URL = "https://livescore-api-kpad.onrender.com"
LOCAL_TZ = ZoneInfo("Africa/Lagos")
FINISHED = {"FT", "AET", "AP", "AOT"}
NOT_PLAYED = {"Postp.", "Canc.", "Abn.", "Susp.", "Int."}

st.set_page_config(page_title="Live Scores", page_icon="🏀")

st.markdown(
    """
<style>
.league {font-weight:700; font-size:0.9rem; padding:8px 12px; margin-top:16px;
         border-left:4px solid currentColor;}
.league.c0 {background:rgba(30,136,229,0.14); color:#1e88e5;}
.league.c1 {background:rgba(67,160,71,0.14); color:#43a047;}
.league.c2 {background:rgba(245,124,0,0.14); color:#f57c00;}
.league.c3 {background:rgba(171,71,188,0.14); color:#ab47bc;}
.row {display:grid; grid-template-columns:78px 1fr 60px 1fr; align-items:center;
      gap:6px; padding:10px 12px; border-bottom:1px solid rgba(128,128,128,0.2);}
.status {font-size:0.8rem; opacity:0.7;}
.status.up {color:#1e88e5; font-weight:600; opacity:1;}
.status.fin {color:#43a047; font-weight:600; opacity:1;}
.status.live {color:#e53935; font-weight:700; opacity:1;}
.status.live::before {content:""; display:inline-block; width:7px; height:7px;
        border-radius:50%; background:#e53935; margin-right:5px; animation:pulse 1.4s infinite;}
.eta {display:block; font-size:0.7rem; font-weight:400; opacity:0.8;}
@keyframes pulse {0% {opacity:1;} 50% {opacity:0.25;} 100% {opacity:1;}}
.team {font-size:0.95rem;}
.team.home {text-align:right;}
.team.w {font-weight:700;}
.team.l {opacity:0.6;}
.score {text-align:center; font-weight:700; border-radius:6px; padding:2px 0;
        background:rgba(128,128,128,0.15);}
.score.live {background:rgba(229,57,53,0.15); color:#e53935;}
.score.up {opacity:0.5;}
.stats {display:flex; gap:8px; margin:6px 0 10px;}
.stat {flex:1; text-align:center; padding:8px 4px; border-radius:10px; font-size:0.8rem;}
.stat b {display:block; font-size:1.3rem;}
.stat.live {background:rgba(229,57,53,0.14);}
.stat.live b {color:#e53935;}
.stat.up {background:rgba(30,136,229,0.14);}
.stat.up b {color:#1e88e5;}
.stat.fin {background:rgba(67,160,71,0.14);}
.stat.fin b {color:#43a047;}
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


def game_kind(game):
    status = (game.get("status") or "").strip()
    if status == "NS":
        return "upcoming"
    if status in FINISHED:
        return "finished"
    if status in NOT_PLAYED:
        return "off"
    return "live"  # HT, 45', Q2, and so on


def eta_text(game):
    local = to_local(game.get("start_time"))
    if local is None:
        return ""
    minutes = int((local - datetime.now(LOCAL_TZ)).total_seconds() // 60)
    if minutes < 0:
        return "due"
    if minutes >= 360:
        return ""
    hours, mins = divmod(minutes, 60)
    return f"in {hours}h {mins:02d}m" if hours else f"in {mins}m"


def status_label(game, show_date):
    kind = game_kind(game)
    status = game.get("status") or ""
    if kind == "upcoming":
        local = to_local(game.get("start_time"))
        if local is None:
            return "NS", "up", ""
        fmt = "%d %b %H:%M" if show_date else "%H:%M"
        return local.strftime(fmt), "up", ("" if show_date else eta_text(game))
    if kind == "finished":
        return status, "fin", ""
    if kind == "live":
        return status, "live", ""
    return status, "", ""


def summary(games):
    counts = {"live": 0, "upcoming": 0, "finished": 0}
    for game in games:
        kind = game_kind(game)
        if kind in counts:
            counts[kind] += 1

    st.markdown(
        '<div class="stats">'
        f'<div class="stat live"><b>{counts["live"]}</b>Live now</div>'
        f'<div class="stat up"><b>{counts["upcoming"]}</b>Upcoming</div>'
        f'<div class="stat fin"><b>{counts["finished"]}</b>Finished</div>'
        "</div>",
        unsafe_allow_html=True,
    )


def league_color(title):
    return sum(ord(ch) for ch in title) % 4


def arrange(items):
    """Live first, then upcoming by kickoff time, then finished (latest first)."""
    items = sorted(items, key=lambda g: g.get("start_time") or "")
    live = [g for g in items if game_kind(g) == "live"]
    upcoming = [g for g in items if game_kind(g) == "upcoming"]
    finished = [g for g in items if game_kind(g) == "finished"][::-1]
    other = [g for g in items if game_kind(g) == "off"]
    return live + upcoming + finished + other


def league_order(items):
    kinds = [game_kind(g) for g in items]
    if "live" in kinds:
        return (0, "")
    kickoffs = [
        g.get("start_time") or "~" for g in items if game_kind(g) == "upcoming"
    ]
    if kickoffs:
        return (1, min(kickoffs))
    return (2, "")


def render(games, show_date):
    leagues = {}
    for game in games:
        key = (game.get("country") or "", game.get("league") or "Other")
        leagues.setdefault(key, []).append(game)

    ordered = sorted(leagues.items(), key=lambda item: league_order(item[1]))

    parts = []
    for (country, league), items in ordered:
        title = f"{country} · {league}" if country else league
        parts.append(
            f'<div class="league c{league_color(title)}">{html.escape(title)}</div>'
        )

        for game in arrange(items):
            label, css, eta = status_label(game, show_date)
            home_score, away_score = game["home_score"], game["away_score"]
            if home_score is None or away_score is None:
                score = "-"
            else:
                score = f"{home_score} - {away_score}"

            home_cls, away_cls = "", ""
            if (
                css == "fin"
                and home_score is not None
                and away_score is not None
                and home_score != away_score
            ):
                home_cls = " w" if home_score > away_score else " l"
                away_cls = " w" if away_score > home_score else " l"

            eta_html = f'<span class="eta">{html.escape(eta)}</span>' if eta else ""
            parts.append(
                f'<div class="row">'
                f'<div class="status {css}">{html.escape(label)}{eta_html}</div>'
                f'<div class="team home{home_cls}">{html.escape(game["home"])}</div>'
                f'<div class="score {css}">{score}</div>'
                f'<div class="team away{away_cls}">{html.escape(game["away"])}</div>'
                f"</div>"
            )

    st.markdown("".join(parts), unsafe_allow_html=True)


st.title("Live Scores")

if "page" not in st.session_state:
    st.session_state.page = "scores"


@st.fragment(run_every=30)
def show_games(sport, team, day_text, view):
    try:
        games = load_games(sport, team, day_text)
    except requests.RequestException:
        st.error("Could not reach the API. It may be waking up, so try again in a minute.")
        return

    if not games:
        st.info("No games found.")
        return

    summary(games)
    st.caption(
        f"Updated {datetime.now(LOCAL_TZ).strftime('%H:%M:%S')} · refreshes every 30 seconds"
    )

    if view != "All":
        games = [g for g in games if game_kind(g) == view.lower()]
    if not games:
        st.info(f"No {view.lower()} games.")
        return

    render(games, show_date=bool(team))


def scores_page():
    col1, col2 = st.columns(2)
    sport = col1.selectbox("Sport", ["soccer", "basketball"], key="scores_sport")
    team = col2.text_input(
        "Search a team", help="Shows all saved games for that team", key="scores_team"
    )

    when = st.radio(
        "Day",
        ["Yesterday", "Today", "Tomorrow", "Pick date"],
        index=1,
        horizontal=True,
        label_visibility="collapsed",
        key="scores_when",
    )
    today = datetime.now(LOCAL_TZ).date()
    if when == "Yesterday":
        day = today - timedelta(days=1)
    elif when == "Tomorrow":
        day = today + timedelta(days=1)
    elif when == "Pick date":
        day = st.date_input("Date", value=today, format="YYYY-MM-DD", key="scores_day")
    else:
        day = today

    view = st.radio(
        "Show",
        ["All", "Live", "Upcoming", "Finished"],
        horizontal=True,
        label_visibility="collapsed",
        key="scores_view",
    )

    btn1, btn2 = st.columns(2)
    if btn1.button("Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    if btn2.button("Analysis", use_container_width=True):
        st.session_state.page = "analysis"
        st.rerun()

    show_games(sport, team.strip(), day.isoformat(), view)


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
            st.caption("AI-generated estimate, not a guarantee. It can be wrong or out of date. Betting involves risk, so only bet what you can afford to lose (18+).")
        elif response.status_code == 429:
            st.warning("The daily analysis limit has been reached. Try again tomorrow.")
        else:
            st.error("Analysis is unavailable right now.")


if st.session_state.page == "analysis":
    analysis_page()
else:
    scores_page()