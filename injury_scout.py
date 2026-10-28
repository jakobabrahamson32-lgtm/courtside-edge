#!/usr/bin/env python3
"""Best-effort NBA/NFL injury scout. Never substitutes unknown for healthy.
Usage: python3 injury_scout.py --nfl (or --nba / both)
Uses ESPN public JSON endpoints; availability and response schema can change.
"""
import argparse, csv, datetime as dt, json, re, sys, unicodedata
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parent
BASE='https://site.api.espn.com/apis/site/v2/sports'
HEADERS={'User-Agent':'CourtsideEdge/1.0 (personal injury monitoring)'}
FIELDS=['Player','Team','Status','Detail','Source','CheckedAt']

def get(url):
    r=requests.get(url,headers=HEADERS,timeout=15)
    r.raise_for_status()
    return r.json()

def norm(s):
    s=unicodedata.normalize('NFKD',str(s).casefold())
    return ''.join(c for c in s if c.isalnum() and not unicodedata.combining(c))

def status(text):
    t=str(text or '').lower().strip()
    if any(x in t for x in ['out for season','season-ending','injured reserve','reserve/injured','inactive','ruled out']) or t=='out':return 'OUT'
    if 'doubtful' in t:return 'DOUBTFUL'
    if 'questionable' in t or 'game-time decision' in t or t=='gtd':return 'QUESTIONABLE'
    if 'probable' in t:return 'PROBABLE'
    if t in ('active','available','healthy','full participant'):return 'AVAILABLE'
    if t in ('day-to-day','day to day','limited','injured','injury','unknown'):return 'REVIEW'
    return 'REVIEW'

def parse_entries(data,source,now):
    """Conservatively parse known ESPN injury layouts; never infer healthy."""
    results=[]
    groups=data if isinstance(data,list) else (data.get('injuries') or data.get('items') or [])
    if isinstance(groups,dict):groups=list(groups.values())
    if not isinstance(groups,list):return results
    for group in groups:
        if not isinstance(group,dict):continue
        team=group.get('team',{})
        if isinstance(team,dict):team=team.get('abbreviation') or team.get('displayName') or ''
        entries=group.get('injuries') or group.get('items') or [group]
        if not isinstance(entries,list):continue
        for entry in entries:
            if not isinstance(entry,dict):continue
            athlete=entry.get('athlete') or entry.get('player') or {}
            if isinstance(athlete,str):name=athlete
            elif isinstance(athlete,dict):name=athlete.get('displayName') or athlete.get('fullName') or athlete.get('name') or ''
            else:name=''
            name=name or entry.get('displayName') or entry.get('playerName') or ''
            if not name or not isinstance(name,str):continue
            raw=entry.get('status') or entry.get('type') or entry.get('designation') or ''
            if isinstance(raw,dict):raw=raw.get('description') or raw.get('name') or raw.get('abbreviation') or ''
            detail=entry.get('details') or entry.get('detail') or entry.get('description') or ''
            if isinstance(detail,dict):detail=detail.get('detail') or detail.get('description') or ''
            team2=entry.get('team') or team
            if isinstance(team2,dict):team2=team2.get('abbreviation') or team2.get('displayName') or ''
            results.append(dict(Player=name,Team=str(team2 or ''),Status=status(raw),Detail=str(detail or raw),Source=source,CheckedAt=now))
    return results

def scout(sport):
    league='football/nfl' if sport=='NFL' else 'basketball/nba'
    urls=[f'{BASE}/{league}/injuries',f'{BASE}/{league}/injuries?limit=500']
    now=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
    errors=[];rows=[]
    for url in urls:
        try:
            data=get(url)
            rows=parse_entries(data,url,now)
            if rows:break
            errors.append(f'{url}: returned no parseable player injury records')
        except (requests.RequestException,ValueError) as e:errors.append(f'{url}: {e}')
    if not rows:
        print(f'WARNING {sport}: Injury source unavailable or unsupported. Existing injury file NOT overwritten.')
        for e in errors:print('  '+e[:230])
        return False
    dedup={}
    for r in rows:
        key=(norm(r['Player']),norm(r['Team']))
        dedup[key]=r
    output=ROOT/f'{sport.lower()}_injuries.csv'
    temp=output.with_suffix('.tmp')
    with temp.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(dedup.values())
    temp.replace(output)
    print(f'{sport}: saved {len(dedup)} injury reports to {output.name} at {now}')
    print('NOTE: Absence from this file does NOT mean a player is healthy. Confirm official game-day inactives.')
    return True

if __name__=='__main__':
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group()
    g.add_argument('--nfl',action='store_true');g.add_argument('--nba',action='store_true')
    a=p.parse_args();sports=['NFL'] if a.nfl else ['NBA'] if a.nba else ['NBA','NFL']
    sys.exit(0 if all(scout(s) for s in sports) else 1)
