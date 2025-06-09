import streamlit as st
import pandas as pd
from datetime import date
from sqlmodel import select
from db import Match, get_session
from players import get_players, add_player, remove_player

# --- CONSTANTS ---
locations = ["Fifth Street Hermosa", "Kahunas Manhattan Beach", "NOP Hermosa", "SOP Hermosa"]

# --- APP START ---

st.title("🏐 Volleyball Match Tracker")

tab1, tab2, tab3, tab4 = st.tabs(["📋 Match Results", "➕ Match Entry", "📊 Dashboard", "👥 Manage Players"])

# --- MATCH ENTRY TAB ---
with tab2:
    st.header("Add a New Match")

    players = get_players()
    if len(players) < 4:
        st.warning("Add at least 4 players in 'Manage Players' tab first.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            player1 = st.selectbox("Player 1", players)
            player2 = st.selectbox("Player 2", players, index=1)
            score1 = st.number_input("Player 1-2 Score", min_value=0, step=1)
            date_played = st.date_input("Date", value=date.today())
        with col2:
            player3 = st.selectbox("Player 3", players, index=2)
            player4 = st.selectbox("Player 4", players, index=3)
            score2 = st.number_input("Player 3-4 Score", min_value=0, step=1)
            time_of_day = st.radio("Time", ["Morning", "Afternoon"])

        location = st.selectbox("Location", locations)
        notes = st.text_area("Notes")

        if st.button("Add Match"):
            new_match = Match(
                player1=player1,
                player2=player2,
                player3=player3,
                player4=player4,
                score1_2=score1,
                score3_4=score2,
                location=location,
                date=date_played,
                time=time_of_day,
                notes=notes
            )
            with get_session() as session:
                session.add(new_match)
                session.commit()
            st.success("✅ Match added!")

# --- MATCH RESULTS TAB ---
with tab1:
    st.header("Match Results")

    with get_session() as session:
        results = session.exec(select(Match)).all()

    if results:
        df_matches = pd.DataFrame([match.model_dump() for match in results])

        with st.sidebar:
            st.subheader("Filters")
            players = get_players()
            player_filter = st.multiselect("Filter by Player", players)
            pair_filter = st.multiselect("Filter by Player Pair (1-2)", players)
            location_filter = st.multiselect("Filter by Location", locations)
            date_range = st.date_input("Date Range", [])

        filtered_df = df_matches.copy()

        if player_filter:
            filtered_df = filtered_df[
                filtered_df[["player1", "player2", "player3", "player4"]]
                .apply(lambda row: any(p in player_filter for p in row), axis=1)
            ]

        if pair_filter:
            filtered_df = filtered_df[
                filtered_df[["player1", "player2"]]
                .apply(lambda row: any(p in pair_filter for p in row), axis=1)
            ]

        if location_filter:
            filtered_df = filtered_df[filtered_df["location"].isin(location_filter)]

        if len(date_range) == 2:
            start_date, end_date = date_range
            # Convert Timestamp to date for safe comparison
            filtered_df["date"] = pd.to_datetime(filtered_df["date"]).dt.date
            filtered_df = filtered_df[
                (filtered_df["date"] >= start_date) &
                (filtered_df["date"] <= end_date)
            ]

        st.dataframe(filtered_df.drop(columns=["id"]), use_container_width=True)
    else:
        st.info("No matches recorded yet.")

# --- DASHBOARD TAB ---
with tab3:
    st.header("📊 Match History Dashboard")

    with get_session() as session:
        results = session.exec(select(Match)).all()

    if not results:
        st.info("No match data yet.")
    else:
        df = pd.DataFrame([m.model_dump() for m in results])
        df["date"] = pd.to_datetime(df["date"]).dt.date

        st.subheader("📌 Summary Stats")
        st.write(f"**Total Matches:** {len(df)}")
        st.write(f"**Unique Locations Played:** {df['location'].nunique()}")

        st.subheader("🏐 Matches Played per Player")
        players = get_players()
        player_counts = pd.Series(0, index=players)
        for col in ["player1", "player2", "player3", "player4"]:
            player_counts += df[col].value_counts()

        st.bar_chart(player_counts)

        st.subheader("🥇 Wins by Pair")
        pair_win_counts = pd.Series(0, index=["Player 1-2 Wins", "Player 3-4 Wins"])
        pair_win_counts["Player 1-2 Wins"] = (df["score1_2"] > df["score3_4"]).sum()
        pair_win_counts["Player 3-4 Wins"] = (df["score3_4"] > df["score1_2"]).sum()
        st.bar_chart(pair_win_counts)

        st.subheader("📊 Average Score by Pair")
        avg_scores = pd.DataFrame({
            "Avg Score": [df["score1_2"].mean(), df["score3_4"].mean()]
        }, index=["Player 1-2", "Player 3-4"])
        st.bar_chart(avg_scores)

        st.subheader("📈 Matches Over Time")
        matches_by_date = df.groupby("date").size()
        st.line_chart(matches_by_date)

# --- MANAGE PLAYERS TAB ---
with tab4:
    st.header("👥 Manage Players")

    new_player = st.text_input("Add New Player Name")
    if st.button("Add Player"):
        if new_player.strip():
            add_player(new_player.strip())
            st.success(f"✅ Added {new_player.strip()}")
        else:
            st.warning("Player name cannot be empty.")

    st.subheader("Current Players")
    current_players = get_players()
    st.write(current_players)

    remove_name = st.selectbox("Remove Player", options=[""] + current_players)
    if st.button("Remove Player") and remove_name:
        remove_player(remove_name)
        st.success(f"✅ Removed {remove_name}")
