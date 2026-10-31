
from nba_api.stats.endpoints import (
    leaguegamelog,
    scoreboardv3
)
from datetime import datetime
import pandas as pd
from statistics import NormalDist
import argparse
import time
from requests.exceptions import RequestException

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
    today = datetime.now(__import__("zoneinfo").ZoneInfo("America/New_York")).strftime("%m/%d/%Y")

    print("Checking NBA games for:", today)

    # ESPN schedule avoids the frequently blocked NBA Stats scoreboard endpoint.
    import requests
    from zoneinfo import ZoneInfo
    eastern_today = datetime.now(ZoneInfo('America/New_York')).strftime('%Y%m%d')
    response = requests.get(
        'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard',
        params={'dates': eastern_today, 'limit': 100}, timeout=25
    )
    response.raise_for_status()
    events = response.json().get('events', [])
    team_abbreviations = set()
    for event in events:
        for competition in event.get('competitions', []):
            for competitor in competition.get('competitors', []):
                abbreviation = competitor.get('team', {}).get('abbreviation', '')
                if abbreviation:
                    team_abbreviations.add(str(abbreviation).upper())
    if not events or not team_abbreviations:
        raise RuntimeError('No NBA games/teams in ESPN scoreboard; projections preserved')
    print(f'ESPN scoreboard: {len(events)} games, {len(team_abbreviations)} teams')
    if True:
        print("Games today:", len(events))
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
        
        # Get current season player game logs
        data = None
        for attempt in range(1, 4):
            try:
                data = leaguegamelog.LeagueGameLog(
                    season="2026-27", season_type_all_star="Regular Season",
                    player_or_team_abbreviation="P", timeout=60
                )
                break
            except RequestException as exc:
                if attempt == 3:
                    raise RuntimeError("NBA game logs unavailable after 3 attempts; old projections preserved") from exc
                print(f"NBA game logs request failed (attempt {attempt}/3); retrying...", flush=True)
                time.sleep(3 * attempt)

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
            stats["TEAM_ABBREVIATION"].isin(team_abbreviations)
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
