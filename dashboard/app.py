from datetime import date
from urllib.parse import quote

import pandas as pd
import requests
import streamlit as st

# Replace with your own Render URL (no slash at the end)
API_URL = "https://livescore-api-kpad.onrender.com"

STATUS_NAMES = {
    "NS": "Not started",
    "FT": "Finished",
}

st.set_page_config(page_title="Live Scores", page_icon="🏀")
st.title("Live Scores")

sport = st.selectbox("Sport", ["basketball", "soccer"])
team = st.text_input("Search a team (optional, ignores the date)")
day = st.date_input("Date", value=None, format="YYYY-MM-DD")

if st.button("Search"):
    if team:
        # A team search shows ALL saved games for that team, on any date
        url = f"{API_URL}/games/{sport}/team/{quote(team)}"
        params = {}
    else:
        # No team typed: show every game on the chosen date
        url = f"{API_URL}/games/{sport}"
        params = {"day": day.isoformat() if day else {}}

    try:
        with st.spinner("Loading..."):
            response = requests.get(url, params=params, timeout=60)
    except requests.RequestException:
        st.error("Could not reach the API. It may be waking up, so try again in a minute.")
        st.stop()

    if response.status_code == 404:
        st.warning("No games found.")
    elif not response.ok:
        st.error(f"The API returned an error ({response.status_code}).")
    else:
        games = response.json()

        rows = []
        for game in games:
            if game["home_score"] is None or game["away_score"] is None:
                score = "-"
            else:
                score = f"{game['home_score']} - {game['away_score']}"

            rows.append({
                "Date": game.get("game_date", ""),
                "Home": game["home"],
                "Score": score,
                "Away": game["away"],
                "Status": STATUS_NAMES.get(game["status"], game["status"]),
            })

        st.write(f"{len(rows)} games")
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)