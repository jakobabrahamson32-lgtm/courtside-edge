"""Courtside Edge NFL weekly player-prop baseline projections.
Requires: pip install nflreadpy pandas pyarrow
Run: python3 nfl_model.py --current-weight 0.60
Uses nflverse regular-season weekly stats. Does not infer injury status or opponents.
"""
from pathlib import Path
import argparse
import pandas as pd

ROOT = Path(__file__).resolve().parent
STAT_COLS = {
    'Passing Yards': 'passing_yards',
    'Passing TDs': 'passing_tds',
    'Interceptions': 'passing_interceptions',
    'Rushing Yards': 'rushing_yards',
    'Rushing Attempts': 'carries',
    'Receiving Yards': 'receiving_yards',
    'Receptions': 'receptions',
    'Receiving TDs': 'receiving_tds',
    'Rushing TDs': 'rushing_tds',
    'Passing Attempts': 'attempts',
    'Passing Completions': 'completions',
    'Passing Interceptions': 'passing_interceptions',
    'Targets': 'targets',
    'Receiving Air Yards': 'receiving_air_yards',
    'Fumbles Lost': 'sack_fumbles_lost',
}

def build(current_weight=0.60, season=2026):
    if not 0 <= current_weight <= 1:
        raise ValueError('Current weight must be between 0 and 1')
    try:
        import nflreadpy as nfl
    except ImportError as exc:
        raise RuntimeError('Install NFL data support: python3 -m pip install nflreadpy pyarrow') from exc
    print(f'Loading nflverse weekly stats for {season-1} and {season}...')
    raw = nfl.load_player_stats([season-1, season], summary_level='week').to_pandas()
    if raw.empty:
        raise RuntimeError('NFL data source returned no rows. Existing files were not changed.')
    player_col = next((c for c in ['player_name','player_display_name','player'] if c in raw), None)
    team_col = next((c for c in ['team','recent_team'] if c in raw), None)
    id_col = next((c for c in ['player_id','gsis_id'] if c in raw), None)
    if not player_col or not team_col or not id_col or 'season' not in raw or 'week' not in raw:
        raise RuntimeError('Unexpected NFL data columns: ' + ', '.join(raw.columns))
    if 'season_type' in raw:
        raw = raw[raw['season_type'].astype(str).str.upper().isin(['REG','REGULAR'])]
    raw['season'] = pd.to_numeric(raw['season'], errors='coerce')
    raw['week'] = pd.to_numeric(raw['week'], errors='coerce')
    raw = raw.dropna(subset=[id_col,'season','week'])
    raw = raw.sort_values(['season','week'])
    current = raw[raw['season']==season]
    previous = raw[raw['season']==season-1]
    if current.empty:
        raise RuntimeError(f'No current-season ({season}) NFL games found. Existing files were not changed.')
    rows = []
    for pid, history in current.groupby(id_col):
        history = history.sort_values('week')
        old = previous[previous[id_col] == pid]
        latest = history.iloc[-1]
        name, team = str(latest[player_col]), str(latest[team_col])
        if name.lower() in ('nan','none') or team.lower() in ('nan','none'):
            continue
        for stat, column in STAT_COLS.items():
            if column not in raw:
                continue
            curr_values = pd.to_numeric(history[column], errors='coerce').dropna()
            prev_values = pd.to_numeric(old[column], errors='coerce').dropna()
            if curr_values.empty:
                continue
            # Current-season last five games (recent form), blended with prior season average.
            current_avg = curr_values.tail(5).mean()
            prev_avg = prev_values.mean() if len(prev_values) else None
            effective_weight = current_weight if prev_avg is not None else 1.0
            projection = effective_weight * current_avg + (1-effective_weight) * (prev_avg if prev_avg is not None else 0)
            rows.append({'Player':name,'Team':team,'PlayerID':str(pid),'Stat':stat,
                         'Projection':round(float(projection),2),
                         'CurrentSeasonAvg':round(float(curr_values.mean()),2),
                         'PreviousSeasonAvg':round(float(prev_avg),2) if prev_avg is not None else None,
                         'Last5Avg':round(float(curr_values.tail(5).mean()),2),
                         'Last10Avg':round(float(curr_values.tail(10).mean()),2),
                         'Games':len(curr_values),'Season':season,
                         'CurrentWeight':effective_weight})
    # Derived markets use actual weekly numerator/denominator data, not a
    # quotient of unrelated season totals. Only add when both fields exist.
    derived = {
        'Completion Percentage': ('completions','attempts',100.0),
        'Yards Per Pass Attempt': ('passing_yards','attempts',1.0),
        'Yards Per Reception': ('receiving_yards','receptions',1.0),
    }
    for pid, history in current.groupby(id_col):
        history=history.sort_values('week')
        old=previous[previous[id_col].eq(pid)]
        latest=history.iloc[-1]
        for stat,(numerator,denominator,multiplier) in derived.items():
            if numerator not in raw or denominator not in raw:
                continue
            def game_values(frame):
                n=pd.to_numeric(frame[numerator],errors='coerce')
                d=pd.to_numeric(frame[denominator],errors='coerce')
                return (n.div(d.where(d.gt(0)))*multiplier).dropna()
            current_values=game_values(history)
            previous_values=game_values(old)
            if current_values.empty:
                continue
            prior=previous_values.mean() if not previous_values.empty else None
            weight=current_weight if prior is not None else 1.0
            projection=weight*current_values.tail(5).mean()+(1-weight)*(prior if prior is not None else 0)
            rows.append({'Player':str(latest[player_col]),'Team':str(latest[team_col]),
                'PlayerID':str(pid),'Stat':stat,'Projection':round(float(projection),2),
                'CurrentSeasonAvg':round(float(current_values.mean()),2),
                'PreviousSeasonAvg':round(float(prior),2) if prior is not None else None,
                'Last5Avg':round(float(current_values.tail(5).mean()),2),
                'Last10Avg':round(float(current_values.tail(10).mean()),2),
                'Games':len(current_values),'Season':season,'CurrentWeight':weight})
    out = pd.DataFrame(rows)
    if out.empty:
        raise RuntimeError('No usable NFL projections. Existing files were not changed.')
    dest = ROOT / 'nfl_projections.csv'
    dest.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(dest, index=False)
    print(f'Saved {len(out)} NFL player-stat projections to {dest}')
    print('Note: These are statistical baselines, not matchup/injury-adjusted predictions.')
    return out

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--current-weight',type=float,default=.60)
    parser.add_argument('--season',type=int,default=2026)
    args=parser.parse_args()
    build(args.current_weight,args.season)
