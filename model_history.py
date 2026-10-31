#!/usr/bin/env python3
"""Immutable pregame model snapshots for Courtside Edge.

Run after the comparison scripts. Never overwrite a saved pick with later
line/projection changes. A future settlement job can attach actual results.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
FIELDS = [
    "PredictionID", "CapturedAtUTC", "Sport", "GameStartsAtUTC",
    "Player", "Team", "Stat", "Sportsbook", "Line", "Projection",
    "Difference", "Direction", "ModelVersion", "Result", "Actual", "SettledAtUTC",
]
SOURCES = {
    "NBA": "nba_prizepicks_comparison.csv",
    "NFL": "nfl_comparison.csv",
}

def snapshot(sport: str, now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    path = ROOT / SOURCES[sport]
    if not path.exists():
        print(f"{sport}: missing {path.name}; no snapshots")
        return 0
    df = pd.read_csv(path)
    required = {"Player", "Team", "Stat", "PrizePicksLine", "ModelProjection"}
    if not required.issubset(df.columns):
        print(f"{sport}: missing required comparison columns; no snapshots")
        return 0
    output = ROOT / "model_history.csv"
    existing = []
    if output.exists():
        with output.open(newline="", encoding="utf-8") as handle:
            existing = list(csv.DictReader(handle))
    ids = {r["PredictionID"] for r in existing}
    additions = []
    for _, item in df.iterrows():
        player, stat = str(item["Player"]).strip(), str(item["Stat"]).strip()
        team = str(item["Team"]).strip()
        line = pd.to_numeric(item["PrizePicksLine"], errors="coerce")
        projection = pd.to_numeric(item["ModelProjection"], errors="coerce")
        if not player or player.lower() == "nan" or pd.isna(line) or pd.isna(projection):
            continue
        # Without a verified kickoff, cannot establish that this is a pregame prediction.
        kickoff_raw = item.get("GameStartsAt", None)
        kickoff = pd.to_datetime(kickoff_raw, utc=True, errors="coerce")
        if pd.isna(kickoff):
            continue
        kickoff_dt = kickoff.to_pydatetime()
        if now >= kickoff_dt:
            continue
        game_time = kickoff_dt.isoformat()
        # The first pregame observation wins; later reruns never revise it.
        identity = "|".join([sport, game_time, player.casefold(), team.casefold(), stat.casefold(), "PrizePicks"])
        pid = hashlib.sha256(identity.encode()).hexdigest()[:24]
        if pid in ids:
            continue
        difference = round(float(projection) - float(line), 3)
        additions.append({
            "PredictionID": pid, "CapturedAtUTC": now.isoformat(),
            "Sport": sport, "GameStartsAtUTC": game_time,
            "Player": player, "Team": team, "Stat": stat,
            "Sportsbook": "PrizePicks", "Line": float(line),
            "Projection": float(projection), "Difference": difference,
            "Direction": "OVER" if difference > 0 else "UNDER" if difference < 0 else "EVEN",
            "ModelVersion": "baseline-v1", "Result": "PENDING",
            "Actual": "", "SettledAtUTC": "",
        })
        ids.add(pid)
    if additions:
        with output.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            if not existing:
                writer.writeheader()
            writer.writerows(additions)
    print(f"{sport}: saved {len(additions)} new immutable pregame predictions")
    if not additions:
        print("No new eligible pregame predictions (possibly missing kickoff times or games already started).")
    return len(additions)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sport", choices=["NBA", "NFL", "both"], default="both")
    args = parser.parse_args()
    for sport in (["NBA", "NFL"] if args.sport == "both" else [args.sport]):
        snapshot(sport)

if __name__ == "__main__":
    main()
