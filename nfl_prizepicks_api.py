"""Download standard full-game NFL PrizePicks player props from ParlayAPI.
Requires PARLAY_API_KEY environment variable. Does not overwrite on empty/error.
"""
import os
from pathlib import Path
import pandas as pd
import requests

MARKETS = {
 'player_pass_yds':'Passing Yards','player_passing_yards':'Passing Yards',
 'player_pass_tds':'Passing TDs','player_passing_tds':'Passing TDs',
 'player_pass_interceptions':'Interceptions','player_interceptions':'Interceptions',
 'player_rush_yds':'Rushing Yards','player_rushing_yards':'Rushing Yards',
 'player_rush_attempts':'Rushing Attempts','player_rushing_attempts':'Rushing Attempts',
 'player_reception_yds':'Receiving Yards','player_receiving_yards':'Receiving Yards',
 'player_receptions':'Receptions','player_reception_tds':'Receiving TDs',
 'player_receiving_tds':'Receiving TDs',
}

def run():
    key=os.environ.get('PARLAY_API_KEY')
    if not key:
        raise SystemExit('Set PARLAY_API_KEY in Terminal first (same as your NBA script).')
    response=requests.get('https://parlay-api.com/v1/sports/americanfootball_nfl/props',
      headers={'X-API-Key':key},params={'bookmakers':'prizepicks','markets':','.join(MARKETS),'limit':10000},timeout=45)
    response.raise_for_status()
    data=response.json()
    items=data if isinstance(data,list) else data.get('data',data.get('props',[]))
    if not isinstance(items,list):
        raise RuntimeError('Unexpected API response format. Existing CSV was not overwritten.')
    rows=[]
    unknown=set()
    for item in items:
        if not isinstance(item,dict) or str(item.get('bookmaker','')).lower()!='prizepicks':
            continue
        if str(item.get('odds_type','')).lower()!='standard' or item.get('period') not in ('FULL',None):
            continue
        market=item.get('market_key','')
        stat=MARKETS.get(market)
        if not stat:
            unknown.add(str(market));continue
        rows.append({'Player':item.get('player'),'Team':item.get('team',''),
                     'Stat':stat,'SportsbookLine':item.get('line'),
                     'GameStartsAt':item.get('commence_time')})
    df=pd.DataFrame(rows)
    if df.empty:
        print('No supported standard NFL props returned; existing CSV preserved.')
        if unknown:print('Unmapped NFL markets:',sorted(unknown))
        return
    df['SportsbookLine']=pd.to_numeric(df['SportsbookLine'],errors='coerce')
    df=df.dropna(subset=['Player','Stat','SportsbookLine'])
    if df.empty:
        print('No valid NFL props; existing CSV preserved.');return
    dest=Path.home()/'Documents'/'nfl_prizepicks_lines.csv'
    df.to_csv(dest,index=False)
    print(f'Saved {len(df)} NFL PrizePicks lines to {dest}')
    if unknown:print('Other market keys (not imported):',sorted(unknown))

if __name__=='__main__':run()
