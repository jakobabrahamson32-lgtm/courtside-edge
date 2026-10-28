#!/usr/bin/env python3
"""Refresh Courtside Edge NBA and NFL datasets with one command.

Run: python3 refresh_all.py
Optional: python3 refresh_all.py --nba   or   --nfl
"""
from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime

ROOT = Path(__file__).resolve().parent
PIPELINES = {
    "NBA": [
        ("NBA projections", "nba_model.py", "todays_nba_projections.csv"),
        ("NBA PrizePicks lines", "ParlayApi.py", "prizepicks_nba_lines.csv"),
        ("NBA comparisons", "nba_prizepicks_model.py", "nba_prizepicks_comparison.csv"),
    ],
    "NFL": [
        ("NFL projections", "nfl_model.py", "nfl_projections.csv"),
        ("NFL PrizePicks lines", "nfl_prizepicks_api.py", "nfl_prizepicks_lines.csv"),
        ("NFL comparisons", "nfl_compare.py", "nfl_comparison.csv"),
    ],
}


def run_pipeline(sport: str) -> bool:
    print(f"\n{'=' * 56}\n{sport} DATA REFRESH\n{'=' * 56}", flush=True)
    for label, script, output in PIPELINES[sport]:
        script_path = ROOT / script
        output_path = ROOT / output
        if not script_path.is_file():
            print(f"ERROR: Missing {script}. Put it in {ROOT}", flush=True)
            return False
        if "PrizePicks" in label and not os.environ.get("PARLAY_API_KEY"):
            print("ERROR: PARLAY_API_KEY is not set in this Terminal session.", flush=True)
            print('Set it with: export PARLAY_API_KEY="YOUR_API_KEY"', flush=True)
            return False

        print(f"\n→ {label} ({script})", flush=True)
        before = output_path.stat().st_mtime_ns if output_path.exists() else None
        try:
            completed = subprocess.run([sys.executable, str(script_path)], cwd=ROOT, check=False)
        except OSError as exc:
            print(f"ERROR: Could not launch {script}: {exc}", flush=True)
            return False
        if completed.returncode != 0:
            print(f"ERROR: {script} exited with code {completed.returncode}. Stopping {sport} refresh.", flush=True)
            return False
        if not output_path.is_file():
            print(f"ERROR: Expected {output} was not created. Stopping {sport} refresh.", flush=True)
            return False
        after = output_path.stat().st_mtime_ns
        if before is not None and after == before:
            print(f"WARNING: {output} was not modified. It may contain old data.", flush=True)
            # Avoid passing off a stale comparison as fresh.
            return False
        try:
            with output_path.open(newline="", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                next(reader, None)
                rows = sum(1 for _ in reader)
        except (OSError, UnicodeError, csv.Error) as exc:
            print(f"ERROR: Cannot read {output}: {exc}", flush=True)
            return False
        if rows == 0:
            print(f"WARNING: {output} has zero data rows. Stopping {sport} refresh.", flush=True)
            return False
        print(f"✓ {output}: {rows:,} rows", flush=True)
    print(f"\n✓ {sport} refresh complete.", flush=True)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh Courtside Edge NBA/NFL data")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--nba", action="store_true", help="Refresh NBA only")
    group.add_argument("--nfl", action="store_true", help="Refresh NFL only")
    args = parser.parse_args()
    sports = ["NBA"] if args.nba else ["NFL"] if args.nfl else ["NBA", "NFL"]
    print(f"COURTSIDE EDGE · {datetime.now().strftime('%Y-%m-%d %I:%M %p')}", flush=True)
    print(f"Working folder: {ROOT}", flush=True)
    results = {sport: run_pipeline(sport) for sport in sports}
    print("\n" + "=" * 56 + "\nREFRESH SUMMARY")
    for sport, ok in results.items():
        print(f"{sport}: {'SUCCESS' if ok else 'FAILED — see message above'}")
    # Injury reports are an optional, independent enrichment step. Fail closed:
    # do not label anyone healthy when a source is missing or stale.
    injury_script = ROOT / "injury_scout.py"
    if injury_script.exists():
        print("\nINJURY SCOUT (best effort)", flush=True)
        for sport in sports:
            result = subprocess.run([sys.executable, str(injury_script), "--" + sport.lower()], cwd=ROOT, check=False)
            if result.returncode:
                print(f"WARNING: {sport} injury feed failed. Verify official reports before games.", flush=True)
    print("Refresh the Streamlit browser tab to load new CSV data.")
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
