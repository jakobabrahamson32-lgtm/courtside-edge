
from nba_api.stats.endpoints import (
    leaguegamelog,
    scoreboardv3
)
from datetime import datetime
import pandas as pd
from statistics import NormalDist
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--current-weight", type=float, default=0.60)
args = parser.parse_args()
if not 0 <= args.current_weight <= 1:
    parser.error("--current-weight must be between 0 and 1")
CURRENT_WEIGHT = args.current_weight
PREVIOUS_WEIGHT = 1 - CURRENT_WEIGHT

print("NBA DAILY PLAYER PROP MODEL")
print("---------------------------")

try:
    today = datetime.now().strftime("%m/%d/%Y")

    print("Checking NBA games for:", today)

    # Get today's games
    scoreboard = scoreboardv3.ScoreboardV3(
        game_date=today,
        timeout=60
    )

    
    games = scoreboard.game_header.get_data_frame()

    print("\nAVAILABLE COLUMNS:")
    print(games.columns.tolist())
    print("\nFIRST GAME:")
    print(games.head(1).to_string())

    if games.empty:
        raise RuntimeError("No NBA games scheduled today; existing projections were not overwritten")

    else:
       
        # Get the teams playing in today's games
        teams = scoreboard.line_score.get_data_frame()

        print("\nTEAM COLUMNS:")
        print(teams.columns.tolist())

        team_ids = set(teams["teamId"])



    
        print("Games today:", len(games))
        print("Downloading player stats...")

        
        print("Downloading previous season averages...")

        from nba_api.stats.endpoints import leaguedashplayerstats

        previous_data = leaguedashplayerstats.LeagueDashPlayerStats(
            season="2025-26",
            season_type_all_star="Regular Season",
            per_mode_detailed="PerGame",
            timeout=90
        )

        previous_stats = previous_data.get_data_frames()[0]
        
        previous_stats = previous_stats.set_index("PLAYER_ID")


        print("Previous season players loaded:", len(previous_stats))
        
        print("Downloading previous season game logs...")

        previous_logs_data = leaguegamelog.LeagueGameLog(
            season="2025-26",
            season_type_all_star="Regular Season",
            player_or_team_abbreviation="P",
            timeout=90
        )

        previous_logs = previous_logs_data.get_data_frames()[0]

        print("Previous season games loaded:", len(previous_logs))

        



        # Get current season player game logs
        data = leaguegamelog.LeagueGameLog(
            season="2026-27",
            season_type_all_star="Regular Season",
            player_or_team_abbreviation="P",
            timeout=90
        )

        stats = data.get_data_frames()[0]

        stats["GAME_DATE"] = pd.to_datetime(
            stats["GAME_DATE"]
        )

        stats = stats.sort_values(
            "GAME_DATE",
            ascending=False
        )

        # Keep only players from today's teams
        stats = stats[
            stats["TEAM_ID"].isin(team_ids)
        ]

     

        
        results = []

        for player_id, player_games in stats.groupby("PLAYER_ID"):

            recent = player_games.head(10)

            player_name = recent.iloc[0]["PLAYER_NAME"]
            team = recent.iloc[0]["TEAM_ABBREVIATION"]

            current_averages = {
                "PTS": recent["PTS"].mean(),
                "REB": recent["REB"].mean(),
                "AST": recent["AST"].mean(),
                "FG3M": recent["FG3M"].mean()
            }

            # Use previous-season data when available
            if player_id in previous_stats.index:
                old = previous_stats.loc[player_id]

                # Handle duplicate player IDs if present
                if isinstance(old, pd.DataFrame):
                    old = old.iloc[0]

                old_games = old["GP"]

                # Only use previous season for players
                # with at least 10 games
                if old_games >= 10:
                    projections_for_player = {
                        stat: (
                            PREVIOUS_WEIGHT * old[stat]
                            + CURRENT_WEIGHT * current_averages[stat]
                        )
                        for stat in current_averages
                    }
                    source = "Blended"
                else:
                    projections_for_player = current_averages
                    source = "Current only"
            else:
                projections_for_player = current_averages
                source = "Current only"

            results.append({
                "Player": player_name,
                "Team": team,
                "Games": len(recent),
                "Points": round(projections_for_player["PTS"], 1),
                "Rebounds": round(projections_for_player["REB"], 1),
                "Assists": round(projections_for_player["AST"], 1),
                "Threes": round(projections_for_player["FG3M"], 1),
                "Method": source
            })



        projections = pd.DataFrame(results)

        if projections.empty:
            raise RuntimeError("No eligible players found; existing projections were not overwritten")

        projections = projections.sort_values(
            "Points",
            ascending=False
        )

        projections.to_csv(
            "todays_nba_projections.csv",
            index=False
        )

        print()
        print("SUCCESS!")
        print("Players analyzed:", len(projections))
        print()
        print(projections.head(20).to_string(index=False))
        print()
        print("Saved to todays_nba_projections.csv")

except Exception as error:
     print("ERROR:", error)
     raise
