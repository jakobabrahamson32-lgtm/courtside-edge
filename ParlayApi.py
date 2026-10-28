
import os
import requests
import pandas as pd
from pathlib import Path

API_KEY = os.environ.get("PARLAY_API_KEY")

if not API_KEY:
    raise SystemExit("Missing PARLAY_API_KEY. Set it in Terminal first.")

url = "https://parlay-api.com/v1/sports/basketball_nba/props"

params = {
    "bookmakers": "prizepicks",
    "markets": "player_points,player_rebounds,player_assists,player_threes",
    "limit": 10000,
}

response = requests.get(
    url,
    headers={"X-API-Key": API_KEY},
    params=params,
    timeout=45
)
response.raise_for_status()

data = response.json()
print("HTTP status:", response.status_code)
print("Response type:", type(data).__name__)

if isinstance(data, dict):
    print("Top-level keys:", list(data.keys()))
    for key, value in data.items():
        print(key, ":", str(value)[:300])
elif isinstance(data, list):
    print("Number of items:", len(data))
    if data:
        print("First item:", str(data[0])[:1000])

# ParlayAPI normally returns a list of prop rows.
if isinstance(data, list):
    rows = data
elif isinstance(data, dict):
    rows = data.get("data", data.get("props", []))
else:
    rows = []

if not isinstance(rows, list):
    raise ValueError("Unexpected API response format.")

market_names = {
    "player_points": "Points",
    "player_rebounds": "Rebounds",
    "player_assists": "Assists",
    "player_threes": "3-PT Made",
    "player_three_pointers": "3-PT Made",
}

results = []

for item in rows:
    if not isinstance(item, dict):
        continue

    if str(item.get("bookmaker", "")).lower() != "prizepicks":
        continue

    # Don't mix quarter/half props with full-game projections.
    if item.get("period") not in ("FULL", None):
        continue

    stat = market_names.get(item.get("market_key"))
    if not stat:
        continue
    
    if str(item.get("odds_type", "")).lower() != "standard":
        continue
    results.append({
    "playerName": item.get("player"),
    "team": item.get("team", ""),
        "stat": stat,
        "line": item.get("line"),
        "league": "NBA",
        "isLive": False,
        "isCombo": False,
        "isPromo": False,
        "oddsType": item.get("odds_type", ""),
        "projectionType": item.get("projection_type", ""),
        "gameStartsAt": item.get("commence_time"),
    })

df = pd.DataFrame(results)

if df.empty:
    raise SystemExit(
        "No matching PrizePicks props returned. "
        "Existing CSV was not overwritten."
    )

df["line"] = pd.to_numeric(df["line"], errors="coerce")
df = df.dropna(subset=["playerName", "stat", "line"])

output = Path.home() / "Documents" / "prizepicks_nba_lines.csv"
df.to_csv(output, index=False)

print(f"Saved {len(df)} PrizePicks props to {output}")
print(df[["playerName", "team", "stat", "line"]].head(10))

