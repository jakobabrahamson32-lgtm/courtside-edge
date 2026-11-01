"""Experimental PrizePicks partner endpoint adapter.

Opt in with PRIZEPICKS_SOURCE=partner. No authentication bypass or user-agent
spoofing. If the endpoint refuses access, fail without replacing saved CSVs.
PrizePicks has not documented this as a supported third-party API.
"""
import os
import re
from pathlib import Path
import pandas as pd
import requests

ROOT=Path(__file__).resolve().parent
URL='https://partner-api.prizepicks.com/projections'
LEAGUES={'NBA':7,'NFL':9}
NBA={'Points':'Points','Rebounds':'Rebounds','Assists':'Assists',
     '3-PT Made':'3-PT Made','3-Pointers Made':'3-PT Made'}
NFL={'player_rec_targets':'Targets','Targets':'Targets','Receiving Targets':'Targets','player_receiving_yards':'Receiving Yards','player_receptions':'Receptions','player_rushing_yards':'Rushing Yards','player_rush_attempts':'Rushing Attempts','player_passing_attempts':'Passing Attempts','player_passing_completions':'Passing Completions','Pass Attempts':'Passing Attempts','Pass Completions':'Passing Completions','Completions':'Passing Completions','Rush Attempts':'Rushing Attempts','Rush Atts':'Rushing Attempts','Rush Yards':'Rushing Yards','Receiving Yds':'Receiving Yards','Rec Yards':'Receiving Yards','Pass Yards':'Passing Yards','Passing Yards':'Passing Yards','Pass Yards':'Passing Yards',
     'Passing TDs':'Passing TDs','Rushing Yards':'Rushing Yards',
     'Rushing Attempts':'Rushing Attempts','Receiving Yards':'Receiving Yards',
     'Receptions':'Receptions','Receiving TDs':'Receiving TDs','Passing Attempts':'Passing Attempts','Passing Completions':'Passing Completions'}

def is_standard(a, name, stat):
    odds=str(a.get('odds_type') or a.get('oddsType') or '').strip().lower()
    if odds != 'standard':return False
    projection=str(a.get('projection_type') or a.get('projectionType') or 'standard').lower()
    if projection not in ('standard',''):return False
    for key in ('is_promo','is_live','is_combo','is_goblin','is_demon','is_discounted','is_flash_sale'):
        if str(a.get(key,False)).lower() in ('true','1'):return False
    if str(a.get('status','')).lower() in ('removed','suspended','closed','inactive'):return False
    description=' '.join(str(x or '') for x in (name,stat,a.get('description'),a.get('projection_type'),a.get('odds_type'))).lower()
    if re.search(r'\b(demon|goblin|promo|discount|flash sale|combo|live|protected play)\b',description):return False
    if re.search(r'\s(?:\+|&|and|vs\.?|/)\s',str(name)):return False
    return True

def attr(obj,key,default=None):
    return (obj or {}).get('attributes',{}).get(key,default)

def fetch(sport, persist=True):
    if sport not in LEAGUES:raise ValueError(sport)
    session=requests.Session()
    rows=[];page=1;seen=set()
    while page<=30:
        response=session.get(URL,params={'league_id':LEAGUES[sport],'per_page':250,'page':page},timeout=30)
        if response.status_code in (401,403,429):
            raise RuntimeError(f'Partner endpoint HTTP {response.status_code}; access not available. Saved data unchanged.')
        response.raise_for_status()
        payload=response.json()
        items=payload.get('data',[])
        if not isinstance(items,list):raise RuntimeError('Unexpected partner endpoint data schema')
        included={(x.get('type'),str(x.get('id'))):x for x in payload.get('included',[]) if isinstance(x,dict)}
        if not items:break
        new=0
        for item in items:
            if not isinstance(item,dict):continue
            identifier=str(item.get('id',''))
            if identifier in seen:continue
            seen.add(identifier);new+=1
            a=item.get('attributes') or {}
            relations=item.get('relationships') or {}
            def related(kind):
                relation=(relations.get(kind) or {}).get('data') or {}
                return included.get((relation.get('type'),str(relation.get('id'))),{})
            player=related('new_player') or related('player')
            name=attr(player,'name') or attr(player,'display_name') or a.get('player_name')
            stat=attr(related('stat_type'),'name') or a.get('stat_type')
            line=a.get('line_score')
            if not name or not stat or line is None:continue
            if not is_standard(a,name,stat):continue
            rows.append({'Player':name,'Team':attr(player,'team',''),
                         'Stat':stat,'Line':line,'GameStartsAt':a.get('start_time') or a.get('game_start_time'),
                         'MarketKey':stat,'Source':'PrizePicks partner endpoint'})
        meta=payload.get('meta') or {}
        pages=meta.get('total_pages')
        if pages is not None and page>=int(pages):break
        if new==0:break
        page+=1
    if not rows:raise RuntimeError('No standard lines parsed; saved CSVs unchanged.')
    frame=pd.DataFrame(rows)
    frame['Line']=pd.to_numeric(frame['Line'],errors='coerce')
    frame=frame.drop_duplicates(subset=['Player','Stat','Line','GameStartsAt'])
    frame=frame.dropna(subset=['Player','Stat','Line'])
    if frame.empty:raise RuntimeError('No usable standard lines; saved CSVs unchanged.')
    if not persist:
        return frame
    if sport=='NBA':
        frame['stat']=frame['Stat'].map(lambda v:NBA.get(v,v))
        output=frame.rename(columns={'Player':'playerName','Team':'team','Line':'line','GameStartsAt':'gameStartsAt'})
        output['league']='NBA';output['isLive']=False;output['isCombo']=False
        output['isPromo']=False;output['oddsType']='standard';output['projectionType']='STANDARD'
        output=output.drop(columns=['Stat','Source'])
        output.to_csv(ROOT/'prizepicks_nba_lines.csv',index=False)
    else:
        frame['Stat']=frame['Stat'].map(lambda v:NFL.get(v,v))
        known=set(NFL.values())
        modelable=frame[frame['Stat'].isin(known)].copy()
        if modelable.empty:raise RuntimeError('No recognized NFL markets; existing comparisons preserved.')
        frame.to_csv(ROOT/'nfl_prizepicks_all_standard.csv',index=False)
        modelable=modelable.rename(columns={'Line':'SportsbookLine'})
        modelable[['Player','Team','Stat','SportsbookLine','GameStartsAt']].to_csv(
            ROOT/'nfl_prizepicks_lines.csv',index=False)
    print(f'Partner endpoint: saved {len(frame)} {sport} standard props from {page} page(s).')
    return frame

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--sport',choices=LEAGUES,required=True)
    fetch(parser.parse_args().sport)
