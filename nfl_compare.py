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
    model_ids = projections.groupby('Key')['PlayerID'].nunique()
    ambiguous = set(model_ids[model_ids > 1].index)
    if ambiguous:
        print(f'Skipping {len(ambiguous)} ambiguous abbreviated player keys.')
    projections = projections[~projections['Key'].isin(ambiguous)].copy()

    # If multiple distinct sportsbook names share the same short key,
    # matching on initial + surname alone is unsafe.
    line_names = lines.groupby('Key')['Player'].nunique()
    bad_keys = set(line_names[line_names > 1].index)
    lines = lines[~lines['Key'].isin(bad_keys)].copy()
    if bad_keys:
        print(f'Skipping {len(bad_keys)} ambiguous sportsbook player keys.')

    # Discard markets with multiple different lines for the same prop.
    line_counts = lines.groupby(['Key', 'StatKey'])['SportsbookLine'].nunique()
    valid = set(line_counts[line_counts == 1].index)
    lines = lines[lines.apply(lambda r: (r['Key'], r['StatKey']) in valid, axis=1)]
    lines = lines.drop_duplicates(['Key', 'StatKey'])

    joined = projections.merge(
        lines[['Key', 'StatKey', 'Player', 'Team', 'SportsbookLine', 'GameStartsAt']],
        on=['Key', 'StatKey'], how='inner', suffixes=('', '_Book')
    )
    print(f'Matched {len(joined)} rows on player initial + surname + prop type (before team filter).')
    if joined.empty:
        print('No matches. Inspect player spellings and the two Stat columns.')
        return pd.DataFrame()

    team_book = joined['Team_Book'].fillna('').astype(str).str.upper().str.strip()
    team_model = joined['Team'].fillna('').astype(str).str.upper().str.strip()
    joined = joined[(team_book == '') | (team_book == team_model)].copy()
    print(f'{len(joined)} matches after optional team verification.')
    if joined.empty:
        print('No matches after team check; inspect team abbreviations.')
        return pd.DataFrame()

    joined['Difference'] = (joined['Projection'] - joined['SportsbookLine']).round(2)
    joined['Direction'] = joined['Difference'].map(lambda x: 'OVER' if x > 0 else 'UNDER' if x < 0 else 'EVEN')
    joined['AbsDifference'] = joined['Difference'].abs()
    joined['Player'] = joined['Player_Book']  # Prefer recognizable full names in dashboard.
    joined = joined.sort_values('AbsDifference', ascending=False)
    columns = ['Player', 'Team', 'PlayerID', 'Stat', 'SportsbookLine', 'Projection',
               'Difference', 'Direction', 'GameStartsAt', 'CurrentSeasonAvg',
               'PreviousSeasonAvg', 'Last5Avg', 'Last10Avg', 'Games']
    result = joined[columns].rename(columns={
        'SportsbookLine': 'PrizePicksLine', 'Projection': 'ModelProjection'
    })
    output = root / 'nfl_comparison.csv'
    result.to_csv(output, index=False)
    print(f'Saved {len(result)} NFL comparisons to {output}')
    return result

if __name__ == '__main__':
    run()
