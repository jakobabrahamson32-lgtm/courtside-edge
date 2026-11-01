"""Match NFL projections to PrizePicks props, including abbreviated nflverse names.
Place in ~/Documents as nfl_compare.py; run: python3 nfl_compare.py
"""
from pathlib import Path
import re
import unicodedata
import pandas as pd

ROOT = Path(__file__).resolve().parent

def clean(value):
    if pd.isna(value):
        return ''
    text = unicodedata.normalize('NFKD', str(value)).casefold()
    text = ''.join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r'\b(jr|sr|ii|iii|iv|v)\b', '', text)
    return re.sub(r'[^a-z0-9]', '', text)

def short_key(value):
    """First initial + full last name: A.Rodgers and Aaron Rodgers -> arodgers."""
    if pd.isna(value):
        return ''
    name = unicodedata.normalize('NFKD', str(value)).casefold()
    name = ''.join(c for c in name if not unicodedata.combining(c))
    name = re.sub(r'\b(jr|sr|ii|iii|iv|v)\b', '', name)
    parts = re.findall(r'[a-z0-9]+', name)
    if len(parts) < 2:
        return clean(value)
    # Model names like A.Rodgers; bookmaker names like Aaron Rodgers.
    return parts[0][0] + ''.join(parts[1:])

def run(root=ROOT):
    projections = pd.read_csv(root / 'nfl_projections.csv')
    lines = pd.read_csv(root / 'nfl_prizepicks_lines.csv')
    result = match_frames(projections, lines)
    if not result.empty:
        output = root / 'nfl_comparison.csv'
        result.to_csv(output, index=False)
        print(f'Saved {len(result)} NFL comparisons to {output}')
    return result

def match_frames(projections, lines):
    """Match in-memory standard sportsbook lines to NFL player projections."""
    projections = projections.copy()
    lines = lines.copy()
    aliases = {
        'rushatts':'Rushing Attempts','rushattempts':'Rushing Attempts',
        'rushingatts':'Rushing Attempts','carries':'Rushing Attempts',
        'rushyards':'Rushing Yards','rushingyds':'Rushing Yards',
        'passatts':'Passing Attempts','passattempts':'Passing Attempts',
        'passingatts':'Passing Attempts','passingattempts':'Passing Attempts',
        'completions':'Passing Completions','passcompletions':'Passing Completions',
        'passingcompletions':'Passing Completions',
        'recs':'Receptions','receptions':'Receptions','receivingreceptions':'Receptions',
        'recyards':'Receiving Yards','receivingyds':'Receiving Yards',
        'receivingyards':'Receiving Yards',
        'playerrectargets':'Targets','rectargets':'Targets',
        'playerreceivingyards':'Receiving Yards','playerreceptions':'Receptions',
        'playerrushingyards':'Rushing Yards','playerrushattempts':'Rushing Attempts',
        'playerpassingattempts':'Passing Attempts','playerpassingcompletions':'Passing Completions'
    }
    # Raw market keys from the partner feed; never interpret player combos as
    # a single-player projection.
    aliases.update({
        'playerpassyds':'Passing Yards',
        'playerpassattempts':'Passing Attempts',
        'playerpasscompletions':'Passing Completions',
        'playerrushyards':'Rushing Yards',
        'playerrushattempts':'Rushing Attempts',
        'playerrectargets':'Targets',
        'playerint':'Interceptions',
        'playerpasstds':'Passing TDs',
        'playerrushtds':'Rushing TDs',
        'playercompletionpercentage':'Completion Percentage',
        'playerrushyardspercarry':'Yards Per Rush Attempt',
        'playerpassplusrushyds':'Passing + Rushing Yards',
        'playerrushplusrecyds':'Rushing + Receiving Yards',
    })
    lines['Stat'] = lines['Stat'].map(lambda v: aliases.get(clean(v),v))
    lines['SportsbookLine'] = pd.to_numeric(lines['SportsbookLine'],errors='coerce')
    lines = lines.dropna(subset=['SportsbookLine'])
    print(f'Loaded {len(projections)} model rows and {len(lines)} sportsbook rows.')
    if projections.empty or lines.empty:
        print('One source is empty. No comparison written.')
        return pd.DataFrame()

    # A short name may represent multiple players (e.g., J.Williams).
    # Never merge those ambiguously; avoid silently attaching the wrong line.
    projections['Key'] = projections['Player'].map(short_key)
    lines['Key'] = lines['Player'].map(short_key)
    projections['StatKey'] = projections['Stat'].map(clean)
    lines['StatKey'] = lines['Stat'].map(clean)
    projections['BookName'] = projections['Player']
    # Verified identity overrides for abbreviated names that collide with
    # unrelated NFL players. IDs below are from the nflverse projection file.
    verified_ids = {'justinjefferson': '00-0036322',
                    'jordanaddison': '00-0038994'}
    lines['VerifiedPlayerID'] = lines['Player'].map(
        lambda name: verified_ids.get(clean(name), ''))
    model_ids = projections.groupby('Key')['PlayerID'].nunique()
    ambiguous = set(model_ids[model_ids > 1].index)
    if ambiguous:
        print(f'{len(ambiguous)} ambiguous abbreviated keys; require a verified ID for those names.')
    projections['AmbiguousKey'] = projections['Key'].isin(ambiguous)
    # Preserve unambiguous names and verified identity matches; never pick
    # one of two people solely from a shared initial and surname.

    # Team aliases from different data providers must be normalized.
    team_alias={'JAX':'JAC','WSH':'WAS','LA':'LAR','STL':'LAR','OAK':'LV','SD':'LAC','ARZ':'ARI','BLT':'BAL','CLV':'CLE','HST':'HOU'}
    def team_key(v):
        t=str(v or '').upper().strip()
        return team_alias.get(t,t)

    # Different full names may share an initial and surname. Keep both and
    # resolve only when their team or verified player ID identifies one player.
    # Discard markets with multiple different lines for the same prop.
    line_counts = lines.groupby(['Key', 'StatKey', 'Player'])['SportsbookLine'].nunique()
    valid = set(line_counts[line_counts == 1].index)
    lines = lines[lines.apply(lambda r: (r['Key'], r['StatKey'],r['Player']) in valid, axis=1)]
    lines = lines.drop_duplicates(['Key', 'StatKey','Player'])

    joined = projections.merge(
        lines[['Key', 'StatKey', 'Player', 'Team', 'SportsbookLine',
               'GameStartsAt', 'VerifiedPlayerID']],
        on=['Key', 'StatKey'], how='inner', suffixes=('', '_Book')
    )
    book_team=joined['Team_Book'].fillna('').map(team_key)
    model_team=joined['Team'].fillna('').map(team_key)
    verified=(joined['VerifiedPlayerID'].ne('') & joined['PlayerID'].astype(str).eq(joined['VerifiedPlayerID']))
    team_verified=book_team.ne('') & book_team.eq(model_team)
    joined=joined[(~joined['AmbiguousKey']) | verified | team_verified].copy()
    print(f'Matched {len(joined)} rows on player initial + surname + prop type (before team filter).')
    if joined.empty:
        print('No matches. Inspect player spellings and the two Stat columns.')
        return pd.DataFrame()

    team_book = joined['Team_Book'].fillna('').map(team_key)
    team_model = joined['Team'].fillna('').map(team_key)
    joined = joined[(team_book == '') | (team_book == team_model)].copy()
    # Reject unresolved duplicate player candidates after team filtering.
    candidate_counts=joined.groupby(['Player_Book','StatKey','SportsbookLine'])['PlayerID'].transform('nunique')
    joined=joined[candidate_counts.eq(1)].copy()
    print(f'{len(joined)} matches after optional team verification.')
    if joined.empty:
        print('No matches after team check; inspect team abbreviations.')
        return pd.DataFrame()

    joined['Difference'] = (joined['Projection'] - joined['SportsbookLine']).round(2)
    joined['Direction'] = joined['Difference'].map(lambda x: 'OVER' if x > 0 else 'UNDER' if x < 0 else 'EVEN')
    joined['AbsDifference'] = joined['Difference'].abs()
    # Conservative, explainable selection score: avoid elevating volatile
    # small-sample props solely because their absolute yardage gap is large.
    joined['Games'] = pd.to_numeric(joined['Games'], errors='coerce').fillna(0)
    joined['Last5Avg'] = pd.to_numeric(joined['Last5Avg'], errors='coerce')
    joined['Last10Avg'] = pd.to_numeric(joined['Last10Avg'], errors='coerce')
    joined['CurrentSeasonAvg'] = pd.to_numeric(joined['CurrentSeasonAvg'], errors='coerce')
    joined['PreviousSeasonAvg'] = pd.to_numeric(joined['PreviousSeasonAvg'], errors='coerce')
    joined['EdgePct'] = (joined['AbsDifference'] / joined['SportsbookLine'].abs().clip(lower=5)).round(3)
    # Recent-form disagreement is a warning, not a fabricated win probability.
    recent = joined['Last5Avg']
    season = joined['CurrentSeasonAvg']
    joined['FormDisagreementPct'] = (
        (recent - season).abs() / joined['SportsbookLine'].abs().clip(lower=5)
    ).fillna(0).round(3)
    joined['SampleFactor'] = (joined['Games'] / 8).clip(lower=0, upper=1)
    joined['ReliabilityScore'] = (
        100 * joined['EdgePct'].clip(upper=0.5)
        * joined['SampleFactor']
        / (1 + joined['FormDisagreementPct'] * 2)
    ).round(2)
    # Flags are deliberately conservative. These are NOT calibrated probabilities.
    joined['PickQuality'] = 'WATCHLIST'
    joined.loc[
        (joined['Games'] >= 5)
        & (joined['EdgePct'] >= 0.12)
        & (joined['FormDisagreementPct'] <= 0.30)
        & (joined['Difference'] != 0), 'PickQuality'
    ] = 'QUALIFIED'
    joined.loc[joined['Games'] < 4, 'PickQuality'] = 'LOW SAMPLE'
    joined.loc[joined['Difference'] == 0, 'PickQuality'] = 'NO EDGE'
    joined['Player'] = joined['Player_Book']  # Prefer recognizable full names in dashboard.
    joined = joined.sort_values(['ReliabilityScore','AbsDifference'], ascending=False)
    columns = ['Player', 'Team', 'PlayerID', 'Stat', 'SportsbookLine', 'Projection',
               'Difference', 'Direction', 'GameStartsAt', 'CurrentSeasonAvg',
               'PreviousSeasonAvg', 'Last5Avg', 'Last10Avg', 'Games',
               'EdgePct', 'FormDisagreementPct', 'ReliabilityScore', 'PickQuality']
    result = joined[columns].rename(columns={
        'SportsbookLine': 'PrizePicksLine', 'Projection': 'ModelProjection'
    })
    return result

if __name__ == '__main__':
    run()
