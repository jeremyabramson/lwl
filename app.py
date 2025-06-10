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
            col1, col2 = st.columns(2)
            with col1:
                p1_team1 = st.selectbox("Team 1 Player 1", player_names, key="p1_team1")
                p2_team1 = st.selectbox("Team 1 Player 2", [p for p in player_names if p != p1_team1], key="p2_team1")
            with col2:
                p1_team2 = st.selectbox("Team 2 Player 1", [p for p in player_names if p not in [p1_team1, p2_team1]], key="p1_team2")
                p2_team2 = st.selectbox("Team 2 Player 2", [p for p in player_names if p not in [p1_team1, p2_team1, p1_team2]], key="p2_team2")

            score_team1 = st.number_input("Team 1 Score", min_value=0)
            score_team2 = st.number_input("Team 2 Score", min_value=0)
            location = st.selectbox("Location", ["Fifth Street Hermosa", "Kahunas Manhattan Beach"])
            date_played = st.date_input("Date", value=date.today())
            time_of_day = st.radio("Time", ["Morning", "Afternoon"])
            notes = st.text_area("Notes")

            if st.button("Add Match"):
                # Check or create teams
                def get_or_create_team(p1, p2):
                    team = session.exec(
                        select(Team).where(
                            ((Team.player1_id == p1.id) & (Team.player2_id == p2.id)) |
                            ((Team.player1_id == p2.id) & (Team.player2_id == p1.id))
                        )
                    ).first()
                    if not team:
                        team = Team(player1_id=p1.id, player2_id=p2.id)
                        session.add(team)
                        session.commit()
                    return team

                p_map = {p.name: p for p in players}
                team1 = get_or_create_team(p_map[p1_team1], p_map[p2_team1])
                team2 = get_or_create_team(p_map[p1_team2], p_map[p2_team2])

                match = Match(
                    team1_id=team1.id,
                    team2_id=team2.id,
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

# --- Match Results ---
with tabs[1]:
    st.header("Match Results")
    with get_session() as session:
        matches = session.exec(select(Match)).all()
        if matches:
            df = []
            for m in matches:
                team1 = session.get(Team, m.team1_id)
                team2 = session.get(Team, m.team2_id)
                p1_team1 = session.get(Player, team1.player1_id).name
                p2_team1 = session.get(Player, team1.player2_id).name
                p1_team2 = session.get(Player, team2.player1_id).name
                p2_team2 = session.get(Player, team2.player2_id).name
                df.append({
                    "Date": m.date,
                    "Time": m.time,
                    "Team 1": f"{p1_team1} & {p2_team1}",
                    "Score T1": m.score_team1,
                    "Team 2": f"{p1_team2} & {p2_team2}",
                    "Score T2": m.score_team2,
                    "Location": m.location,
                    "Notes": m.notes
                })
            st.dataframe(pd.DataFrame(df))
        else:
            st.info("No matches recorded.")

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
