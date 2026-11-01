#!/usr/bin/env python3
"""Settle immutable pregame predictions using completed ESPN game box scores.

Unmatched, ambiguous, unplayed, and unverifiable props remain PENDING.
"""
import csv
import re
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
import requests
import pandas as pd

ROOT = Path(__file__).resolve().parent
HISTORY = ROOT / "model_history.csv"
BASE = "https://site.api.espn.com/apis/site/v2/sports"
SPORT_PATH = {"NBA": "basketball/nba", "NFL": "football/nfl"}
NBA_STAT = {"points": "PTS", "rebounds": "REB", "assists": "AST", "threes": "3PT"}
NFL_STAT = {"passingyards": ("passing", "YDS"),
            "rushingyards": ("rushing", "YDS"),
            "receivingyards": ("receiving", "YDS"),
            "receptions": ("receiving", "REC"),
            "rushingattempts": ("rushing", "CAR"),
            "passingattempts": ("passing", "ATT"),
            "passingcompletions": ("passing", "CMP")}
TEAM_ALIASES = {"PHX": "PHO", "GS": "GSW", "NY": "NYK", "SA": "SAS", "UTAH": "UTA",
                "WSH": "WAS", "JAC": "JAX", "LA": "LAR", "NO": "NOP"}

def normalize(value):
    value = unicodedata.normalize("NFKD", str(value).casefold())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in value if not unicodedata.combining(c)))

def team(value):
    code = str(value or "").upper()
    return TEAM_ALIASES.get(code, code)

def get_json(sport, endpoint, params):
    url = f"{BASE}/{SPORT_PATH[sport]}/{endpoint}"
    response = requests.get(url, params=params, timeout=25,
                            headers={"User-Agent": "CourtsideEdge/1.0"})
    response.raise_for_status()
    return response.json()

def number(raw):
    try:
        return float(str(raw).split("-")[0].replace(",", ""))
    except (ValueError, TypeError):
        return None

def game_stats(sport, event_id):
    data = get_json(sport, "summary", {"event": event_id})
    results = defaultdict(list)
    for entry in data.get("boxscore", {}).get("players", []):
        code = team(entry.get("team", {}).get("abbreviation"))
        for group in entry.get("statistics", []):
            category = normalize(group.get("name") or group.get("displayName") or "")
            labels = [str(label).upper() for label in group.get("labels", [])]
            for row in group.get("athletes", []):
                if row.get("didNotPlay"):
                    continue
                name = normalize(row.get("athlete", {}).get("displayName", ""))
                values = row.get("stats", [])
                if not name or not isinstance(values, list):
                    continue
                stats = dict(zip(labels, values))
                if sport == "NBA":
                    for stat, label in NBA_STAT.items():
                        raw = stats.get(label)
                        if stat == "threes" and raw is None:
                            raw = stats.get("3PM")
                        val = number(raw)
                        if val is not None:
                            results[(name, code, stat)].append(val)
                else:
                    for stat, (required_category, label) in NFL_STAT.items():
                        if required_category not in category:
                            continue
                        raw = stats.get(label)
                        if stat == "passingattempts":
                            raw = stats.get("C/ATT", "").split("/")[-1] if "C/ATT" in stats else stats.get("ATT")
                        if stat == "passingcompletions":
                            raw = stats.get("C/ATT", "").split("/")[0] if "C/ATT" in stats else stats.get("CMP")
                        val = number(raw)
                        if val is not None:
                            results[(name, code, stat)].append(val)
    # Ambiguous duplicates are not settled.
    return {key: values[0] for key, values in results.items()
            if len(values) == 1 or len(set(values)) == 1}

def settle():
    if not HISTORY.exists():
        print("No history file; nothing to settle")
        return
    with HISTORY.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames
        rows = list(reader)
    if not fields or not rows:
        print("History empty; nothing to settle")
        return
    now = datetime.now(timezone.utc)
    pending = defaultdict(list)
    for row in rows:
        if str(row.get("Result", "")).upper() != "PENDING":
            continue
        kickoff = pd.to_datetime(row.get("GameStartsAtUTC"), utc=True, errors="coerce")
        if pd.isna(kickoff) or kickoff.to_pydatetime() >= now:
            continue
        sport = row.get("Sport", "").upper()
        if sport not in SPORT_PATH:
            continue
        pending[(sport, kickoff.strftime("%Y%m%d"))].append(row)
    settled = 0
    for (sport, day), picks in pending.items():
        try:
            events = []
            for offset in (-1, 0, 1):
                date = (datetime.strptime(day, "%Y%m%d") + timedelta(days=offset)).strftime("%Y%m%d")
                events.extend(get_json(sport, "scoreboard", {"dates": date, "limit": 100}).get("events", []))
        except requests.RequestException as exc:
            print(f"{sport} {day} scoreboard unavailable: {exc}")
            continue
        for event in events:
            if not event.get("status", {}).get("type", {}).get("completed", False):
                continue
            start = pd.to_datetime(event.get("date"), utc=True, errors="coerce")
            if pd.isna(start):
                continue
            competitors = [team(c.get("team", {}).get("abbreviation"))
                           for game in event.get("competitions", [])
                           for c in game.get("competitors", [])]
            try:
                actuals = game_stats(sport, event["id"])
            except (requests.RequestException, KeyError, ValueError) as exc:
                print(f"{sport} game {event.get('id')} box score unavailable: {exc}")
                continue
            for row in picks:
                if row["Result"] != "PENDING" or team(row.get("Team")) not in competitors:
                    continue
                kickoff = pd.to_datetime(row.get("GameStartsAtUTC"), utc=True, errors="coerce")
                if pd.isna(kickoff) or abs((kickoff - start).total_seconds()) > 4 * 3600:
                    continue
                key = (normalize(row.get("Player")), team(row.get("Team")), normalize(row.get("Stat")))
                actual = actuals.get(key)
                if actual is None:
                    continue
                try:
                    line = float(row["Line"])
                except (ValueError, TypeError):
                    continue
                direction = str(row.get("Direction", "")).upper()
                if direction not in ("OVER", "UNDER"):
                    continue
                row["Actual"] = actual
                row["Result"] = ("PUSH" if actual == line else
                                 "WIN" if (actual > line) == (direction == "OVER") else "LOSS")
                row["SettledAtUTC"] = now.isoformat()
                settled += 1
    if settled:
        temporary = HISTORY.with_suffix(".tmp")
        with temporary.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        temporary.replace(HISTORY)
    print(f"Results settlement: {settled} verified picks settled; unresolved picks remain PENDING")

if __name__ == "__main__":
    settle()
