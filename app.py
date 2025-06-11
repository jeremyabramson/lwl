import streamlit as st
from db import get_session, init_db
from models import Player, Team, Match
from datetime import date
from sqlmodel import select
import pandas as pd

# Initialize DB
init_db()

st.title("🏐 Volleyball Match Tracker — Teams Edition")

tabs = st.tabs(["➕ Match Entry", "📋 Match Results", "📊 Player/Team Dashboard", "👥 Manage Players"])

# --- Manage Players ---
with tabs[3]:
    st.header("Manage Players")
    with get_session() as session:
        new_player = st.text_input("Add New Player")
        if st.button("Add Player"):
            if new_player.strip():
                session.add(Player(name=new_player.strip()))
                session.commit()
                st.success(f"Added {new_player.strip()}")
        
        players = session.exec(select(Player)).all()
        st.write("**Current Players:**", [p.name for p in players])

# --- Match Entry ---
with tabs[0]:
    st.header("Add a New Match")
    with get_session() as session:
        players = session.exec(select(Player)).all()
        player_names = [p.name for p in players]

        if len(players) < 4:
            st.warning("At least 4 players are required.")
        else:
            teams = session.exec(select(Team)).all()
            team_options = []
            for t in teams:
                p1 = session.get(Player, t.player1_id).name
                p2 = session.get(Player, t.player2_id).name
                team_options.append((t.id, f"{p1} & {p2}"))

            def team_input_block(label, key_prefix, excluded_player_ids=None):
                if excluded_player_ids is None:
                    excluded_player_ids = []

                # Filter available teams based on excluded players
                available_team_options = []
                for t in teams:
                    if t.player1_id not in excluded_player_ids and t.player2_id not in excluded_player_ids:
                        p1 = session.get(Player, t.player1_id).name
                        p2 = session.get(Player, t.player2_id).name
                        available_team_options.append((t.id, f"{p1} & {p2}"))

                mode = st.segmented_control(
                    f"{label} Input Mode",
                    options=["Existing Team", "Pick Players"],
                    default="Existing Team",
                    key=f"{key_prefix}_mode"
                )
                if mode == "Existing Team":
                    if not available_team_options:
                        st.warning(f"No available teams for {label}.")
                        return None, []
                    team_id, team_label = st.selectbox(
                        f"{label} (Existing)",
                        options=available_team_options,
                        format_func=lambda x: x[1],
                        key=f"{key_prefix}_existing"
                    )
                    # Lookup player IDs for exclusion
                    selected_team = next(t for t in teams if t.id == team_id)
                    exclude_ids = [selected_team.player1_id, selected_team.player2_id]
                    return team_id, exclude_ids
                else:
                    available_players = [p for p in players if p.id not in excluded_player_ids]
                    if len(available_players) < 2:
                        st.warning(f"Not enough available players for {label}.")
                        return None, []
                    p1 = st.selectbox(
                        f"{label} Player 1",
                        [p.name for p in available_players],
                        key=f"{key_prefix}_p1"
                    )
                    p1_id = next(p.id for p in available_players if p.name == p1)

                    p2 = st.selectbox(
                        f"{label} Player 2",
                        [p.name for p in available_players if p.name != p1],
                        key=f"{key_prefix}_p2"
                    )
                    p2_id = next(p.id for p in available_players if p.name == p2)

                    team = session.exec(
                        select(Team).where(
                            ((Team.player1_id == p1_id) & (Team.player2_id == p2_id)) |
                            ((Team.player1_id == p2_id) & (Team.player2_id == p1_id))
                        )
                    ).first()
                    if not team:
                        team = Team(player1_id=p1_id, player2_id=p2_id)
                        session.add(team)
                        session.commit()
                    return team.id, [p1_id, p2_id]

            col1, col2 = st.columns(2)
            with col1:
                team1_id, team1_excludes = team_input_block("Team 1", "team1")
            with col2:
                team2_id, team2_excludes = team_input_block("Team 2", "team2", excluded_player_ids=team1_excludes)

            if team1_id and team2_id:
                def team_label(team_id):
                    t = session.get(Team, team_id)
                    p1 = session.get(Player, t.player1_id).name
                    p2 = session.get(Player, t.player2_id).name
                    return f"{p1} & {p2}"

                team1_label = team_label(team1_id)
                team2_label = team_label(team2_id)

                score_team1 = st.number_input(f"{team1_label} score", min_value=0)
                score_team2 = st.number_input(f"{team2_label} score", min_value=0)

                location = st.selectbox("Location", ["Fifth Street Hermosa", "Kahunas Manhattan Beach"])
                date_played = st.date_input("Date", value=date.today())
                time_of_day = st.radio("Time", ["Morning", "Afternoon"])
                notes = st.text_area("Notes")

                if st.button("Add Match"):
                    match = Match(
                        team1_id=team1_id,
                        team2_id=team2_id,
                        score_team1=score_team1,
                        score_team2=score_team2,
                        location=location,
                        date=date_played,
                        time=time_of_day,
                        notes=notes
                    )
                    session.add(match)
                    session.commit()
                    st.success("Match added successfully!")
                    st.experimental_rerun()

# --- Dashboard ---
with tabs[2]:
    st.header("Player & Team Dashboard")
    with get_session() as session:
        matches = session.exec(select(Match)).all()
        if matches:
            players = session.exec(select(Player)).all()
            player_records = {p.name: {"Wins":0, "Losses":0, "Games":0} for p in players}
            team_records = {}

            for m in matches:
                t1 = session.get(Team, m.team1_id)
                t2 = session.get(Team, m.team2_id)
                t1_names = f"{session.get(Player, t1.player1_id).name} & {session.get(Player, t1.player2_id).name}"
                t2_names = f"{session.get(Player, t2.player1_id).name} & {session.get(Player, t2.player2_id).name}"

                team_records.setdefault(t1_names, {"Wins":0, "Losses":0, "Games":0})
                team_records.setdefault(t2_names, {"Wins":0, "Losses":0, "Games":0})

                team_records[t1_names]["Games"] += 1
                team_records[t2_names]["Games"] += 1

                if m.score_team1 > m.score_team2:
                    team_records[t1_names]["Wins"] += 1
                    team_records[t2_names]["Losses"] += 1
                    winners = [t1.player1_id, t1.player2_id]
                    losers = [t2.player1_id, t2.player2_id]
                else:
                    team_records[t2_names]["Wins"] += 1
                    team_records[t1_names]["Losses"] += 1
                    winners = [t2.player1_id, t2.player2_id]
                    losers = [t1.player1_id, t1.player2_id]

                for pid in winners:
                    pname = session.get(Player, pid).name
                    player_records[pname]["Wins"] +=1
                    player_records[pname]["Games"] +=1

                for pid in losers:
                    pname = session.get(Player, pid).name
                    player_records[pname]["Losses"] +=1
                    player_records[pname]["Games"] +=1

            st.subheader("Player Records")
            st.dataframe(pd.DataFrame(player_records).T)

            st.subheader("Team Records")
            st.dataframe(pd.DataFrame(team_records).T)
        else:
            st.info("No match data available.")
