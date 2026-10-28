
import pandas as pd
from pathlib import Path
import unicodedata

print("NBA PRIZEPICKS MODEL")
print("--------------------")

folder = Path(__file__).resolve().parent

nba = pd.read_csv(folder / "todays_nba_projections.csv")
props = pd.read_csv(folder / "prizepicks_nba_lines.csv")

def clean_name(name):
    name = str(name).lower().strip()
    name = unicodedata.normalize("NFKD", name)
    name = "".join(
        c for c in name if not unicodedata.combining(c)
    )
    return name.replace(".", "").replace("'", "")

nba["MatchName"] = nba["Player"].apply(clean_name)
props["MatchName"] = props["playerName"].apply(clean_name)

stat_map = {
    "Points": "Points",
    "Rebounds": "Rebounds",
    "Assists": "Assists",
    "3-PT Made": "Threes"
}

# Convert boolean-like columns safely
def is_false(series):
    return series.astype(str).str.lower().isin(
        ["false", "0"]
    )

# Filter supported props
props = props[
    props["stat"].isin(stat_map)
    & (props["league"].astype(str).str.upper() == "NBA")
    & is_false(props["isLive"])
    & is_false(props["isCombo"])
    & is_false(props["isPromo"])
    & (props["oddsType"].astype(str).str.lower() == "standard")
].copy()

props["ModelStat"] = props["stat"].map(stat_map)

# Only use valid numbers
props["line"] = pd.to_numeric(props["line"], errors="coerce")
props = props.dropna(subset=["line", "playerName"])

# Remove ambiguous NBA player names
nba = nba[
    ~nba["MatchName"].duplicated(keep=False)
].copy()

# Keep one standard line per player and stat
# Conflicting lines are excluded, not guessed.
line_counts = props.groupby(
    ["MatchName", "ModelStat"]
)["line"].nunique()

valid_keys = line_counts[line_counts == 1].index

props = props.set_index(
    ["MatchName", "ModelStat"]
).loc[
    lambda df: df.index.isin(valid_keys)
].reset_index()

props = props.drop_duplicates(
    subset=["MatchName", "ModelStat", "line"]
)

# Convert projections into long format
nba_long = nba.melt(
    id_vars=["Player", "Team", "MatchName"],
    value_vars=["Points", "Rebounds", "Assists", "Threes"],
    var_name="ModelStat",
    value_name="Projection"
)

# Match by player name and stat
matched = props.merge(
    nba_long,
    on=["MatchName", "ModelStat"],
    how="inner"
)

# If ParlayAPI supplies a team, verify it.
# Blank teams are allowed.
if "team" in matched.columns:
    pp_team = (
        matched["team"]
        .astype("string")
        .fillna("")
        .str.upper()
        .str.strip()
    )
    nba_team = (
        matched["Team"]
        .astype("string")
        .fillna("")
        .str.upper()
        .str.strip()
    )
    matched = matched[
        (pp_team == "") | (pp_team == nba_team)
    ].copy()

matched["Projection"] = pd.to_numeric(
    matched["Projection"], errors="coerce"
)
matched = matched.dropna(subset=["Projection"])

matched["Difference"] = (
    matched["Projection"] - matched["line"]
).round(2)

matched["Direction"] = matched["Difference"].apply(
    lambda value: "MORE" if value > 0
    else "LESS" if value < 0
    else "EVEN"
)

matched["AbsDifference"] = matched["Difference"].abs()

matched = matched.sort_values(
    "AbsDifference", ascending=False
)

output = matched[
    ["Player", "Team", "stat", "line",
     "Projection", "Difference", "Direction"]
].copy()

output.columns = [
    "Player", "Team", "Stat", "PrizePicksLine",
    "ModelProjection", "Difference", "Direction"
]

print("\nMatched PrizePicks props:", len(output))

print("\nTOP 25 PROJECTION DIFFERENCES")
print("-----------------------------")
print(output.head(25).to_string(index=False))

# Don't overwrite an existing comparison with empty data
if output.empty:
    print("\nNo matches found.")
    print("Existing comparison CSV was NOT overwritten.")
else:
    destination = folder / "nba_prizepicks_comparison.csv"
    output.to_csv(destination, index=False)
    print("\nSaved to:", destination)
