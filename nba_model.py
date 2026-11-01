"""NBA daily player projections using ESPN scoreboard and box scores.

ESPN-based recent-game baseline. Previous-season blending is intentionally
disabled until a verified historical data source is configured.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent
BASE = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"
HEADERS = {"User-Agent": "CourtsideEdge/1.0"}
STAT_KEYS = {"PTS": "Points", "REB": "Rebounds", "AST": "Assists", "3PM": "Threes", "STL": "Steals", "BLK": "Blocks", "TO": "Turnovers"}
ALIASES = {"PHX": "PHO", "GS": "GSW", "NY": "NYK", "SA": "SAS", "UTAH": "UTA"}

def get_json(url, params=None):
    response = requests.get(url, params=params, headers=HEADERS, timeout=25)
    response.raise_for_status()
    return response.json()

def team_code(value):
    code = str(value or "").upper().strip()
    return ALIASES.get(code, code)

def scoreboard(day):
    data = get_json(BASE + "/scoreboard", {"dates": day.strftime("%Y%m%d"), "limit": 100})
    return data.get("events", [])

def extract_boxscore(event_id, eligible):
    data = get_json(BASE + "/summary", {"event": event_id})
    rows = []
    for team in data.get("boxscore", {}).get("players", []):
        team_abbr = team_code(team.get("team", {}).get("abbreviation"))
        if team_abbr not in eligible:
            continue
        for group in team.get("statistics", []):
            labels = [str(v).upper() for v in group.get("labels", [])]
            for item in group.get("athletes", []):
                athlete = item.get("athlete", {})
                values = item.get("stats", [])
                if not isinstance(values, list) or not labels:
                    continue
                stats = dict(zip(labels, values))
                if not all(k in stats for k in ("PTS", "REB", "AST")):
                    continue
                def number(key):
                    try:
                        return float(stats.get(key, 0))
                    except (TypeError, ValueError):
                        return 0.0
                threes = stats.get("3PT", stats.get("3PM", "0"))
                if isinstance(threes, str) and "-" in threes:
                    threes = threes.split("-", 1)[0]
                try:
                    threes = float(threes)
                except (ValueError, TypeError):
                    threes = 0.0
                if not athlete.get("displayName") or item.get("didNotPlay"):
                    continue
                extra = {}
                for code, label in [("STL","Steals"),("BLK","Blocks"),("TO","Turnovers")]:
                    if code in stats:
                        extra[label] = number(code)
                rows.append({"Player": athlete["displayName"], "Team": team_abbr,
                             "PlayerID": str(athlete.get("id", "")),
                             "Points": number("PTS"), "Rebounds": number("REB"),
                             "Assists": number("AST"), "Threes": threes,
                             "GameID": str(event_id), **extra})
    return rows

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--current-weight", type=float, default=0.6,
                        help="Retained for compatibility; ESPN baseline uses current games only")
    args = parser.parse_args()
    if not 0 <= args.current_weight <= 1:
        parser.error("--current-weight must be between 0 and 1")
    now = datetime.now(ZoneInfo("America/New_York"))
    print("NBA DAILY PLAYER PROP MODEL (ESPN)", flush=True)
    today = scoreboard(now.date())
    eligible = {team_code(c.get("team", {}).get("abbreviation"))
                for event in today
                for game in event.get("competitions", [])
                for c in game.get("competitors", [])}
    eligible.discard("")
    if not today or not eligible:
        raise RuntimeError("No NBA games or team IDs today; existing projections preserved")
    print(f"ESPN scoreboard: {len(today)} games, {len(eligible)} teams", flush=True)

    # Only use completed games before today; avoid leaking in-progress results.
    candidates = {}
    for days_back in range(1, 29):
        day = now.date() - timedelta(days=days_back)
        try:
            events = scoreboard(day)
        except requests.RequestException as exc:
            print(f"Schedule unavailable for {day}: {exc}", flush=True)
            continue
        for event in events:
            if not event.get("status", {}).get("type", {}).get("completed", False):
                continue
            teams = {team_code(c.get("team", {}).get("abbreviation"))
                     for g in event.get("competitions", [])
                     for c in g.get("competitors", [])}
            if teams & eligible and event.get("id"):
                candidates[str(event["id"])] = event
    if not candidates:
        raise RuntimeError("No verified completed recent NBA games; existing projections preserved")
    print(f"Fetching {len(candidates)} completed box scores...", flush=True)
    rows = []
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(extract_boxscore, eid, eligible): eid for eid in candidates}
        for future in as_completed(futures):
            try:
                rows.extend(future.result())
            except (requests.RequestException, ValueError, KeyError) as exc:
                print(f"Box score {futures[future]} unavailable: {exc}", flush=True)
    if not rows:
        raise RuntimeError("No verified ESPN player box-score stats; existing projections preserved")
    df = pd.DataFrame(rows).drop_duplicates(["GameID", "PlayerID", "Team"])
    # Order by event start date, not API completion order.
    df["GameDate"] = df["GameID"].map(
        lambda eid: candidates.get(eid, {}).get("date", ""))
    df = df.sort_values("GameDate", ascending=False)
    results = []
    for (player_id, team), games in df.groupby(["PlayerID", "Team"]):
        recent = games.head(10)
        if not player_id or recent.empty:
            continue
        row = {"Player": recent.iloc[0]["Player"], "Team": team,
               "Games": len(recent), "Method": "ESPN recent games only"}
        for stat in STAT_KEYS.values():
            if stat in recent and recent[stat].notna().any():
                row[stat] = round(float(recent[stat].mean()), 1)
        combinations = {
            "Points + Rebounds": ["Points", "Rebounds"],
            "Points + Assists": ["Points", "Assists"],
            "Rebounds + Assists": ["Rebounds", "Assists"],
            "Points + Rebounds + Assists": ["Points", "Rebounds", "Assists"],
            "Steals + Blocks": ["Steals", "Blocks"],
        }
        for label, fields in combinations.items():
            if all(field in recent and recent[field].notna().all() for field in fields):
                row[label] = round(float(recent[fields].sum(axis=1).mean()), 1)
        results.append(row)
    if not results:
        raise RuntimeError("No eligible player projections; existing CSV preserved")
    output = pd.DataFrame(results).sort_values("Points", ascending=False)
    destination = ROOT / "todays_nba_projections.csv"
    output.to_csv(destination, index=False)
    print(f"Saved {len(output)} ESPN recent-game NBA projections to {destination}", flush=True)
    print("NOTE: Current-only statistical baselines, not previous-season blended or injury adjusted.", flush=True)

if __name__ == "__main__":
    main()
