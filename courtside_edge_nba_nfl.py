"""PROPIFIED — combined NBA + NFL Streamlit dashboard.
Put this file and the companion NFL scripts in ~/Documents.
Run: python3 -m streamlit run courtside_edge_nba_nfl.py
"""
from pathlib import Path
from datetime import datetime, date
import subprocess
import sys
import unicodedata
import pandas as pd
import streamlit as st

st.set_page_config(page_title='Propified | NBA + NFL',page_icon='◉',layout='wide',initial_sidebar_state='auto')
ROOT = Path(__file__).resolve().parent
C={'purple':'#6415D8','deep':'#4C0DB3','lavender':'#EDE3FF','background':'#FAFAFC','text':'#17142F','muted':'#696780','green':'#16A878','red':'#E34D64'}
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Lato:wght@400;700;900&family=Space+Mono:wght@400;700&display=swap');
:root{--ce-purple:#6415D8;--ce-deep:#4C0DB3;--ce-lavender:#EDE3FF;--ce-bg:#FAFAFC;--ce-panel:#FFFFFF;--ce-border:#E5E5EF;--ce-text:#17142F;--ce-muted:#696780}
html,body,[class*="css"],.stApp{font-family:'Lato',sans-serif;color:var(--ce-text)}
.stApp,[data-testid="stAppViewContainer"]{background:#F2EAFF!important;color:var(--ce-text)!important}
[data-testid="stHeader"]{background:rgba(250,250,252,.95)!important}
[data-testid="stSidebar"]{background:linear-gradient(165deg,#D6B8FF 0%,#EEE1FF 54%,#FAF6FF 100%)!important;border-right:1px solid var(--ce-border)!important}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"]{gap:.7rem}
[data-testid="stSidebar"] .stRadio>div[role="radiogroup"]{gap:.3rem}
[data-testid="stSidebar"] .stRadio>div[role="radiogroup"] label{border-radius:11px;padding:9px 12px;transition:background .15s ease,color .15s ease}
[data-testid="stSidebar"] .stRadio>div[role="radiogroup"] label:hover{background:#F3ECFF}
[data-testid="stSidebar"] .stRadio>div[role="radiogroup"] label:has(input:checked){background:#6415D8;color:#FFFFFF!important;font-weight:700}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p{color:#696780}
.block-container{max-width:1400px!important;padding:2rem 2.5rem 5rem!important}
h1,h2,h3,h4{font-family:'Space Mono',monospace!important;color:#17142F!important;letter-spacing:-.035em!important}
h2{font-size:clamp(1.55rem,2.5vw,2.05rem)!important}
h3{font-size:1.2rem!important}
p,span,label{font-family:'Lato',sans-serif}
[data-testid="stMetric"]{background:linear-gradient(135deg,#FFFFFF 30%,#E9D9FF)!important;border:1px solid #B895F5!important;border-radius:17px!important;padding:20px 22px!important;min-height:126px;box-shadow:0 3px 14px rgba(44,24,92,.025)!important}
[data-testid="stMetricLabel"]{color:#696780!important;font-size:.82rem!important}
[data-testid="stMetricValue"]{color:#17142F!important;font-family:'Space Mono',monospace!important;font-size:clamp(1.6rem,2.7vw,2.3rem)!important;letter-spacing:-.045em!important}
[data-testid="stMetricDelta"]{color:#16A878}
[data-testid="stVerticalBlockBorderWrapper"]>div{border:1px solid #E5E5EF!important;background:#FFFFFF!important;border-radius:17px!important}
.stButton button,.stDownloadButton button{border:1px solid #E5E5EF!important;border-radius:11px!important;background:#FFFFFF!important;color:#17142F!important;font-weight:650!important;transition:background .15s,border-color .15s,transform .15s!important}
.stButton button:hover,.stDownloadButton button:hover{border-color:#6415D8!important;background:#F6F1FF!important;color:#4C0DB3!important}
.stButton button[kind="primary"]{background:#6415D8!important;border-color:#6415D8!important;color:#FFFFFF!important}
.stButton button[kind="primary"]:hover{background:#4C0DB3!important}
[data-testid="stSidebar"] .stButton button{background:#6415D8!important;color:white!important;border-color:#6415D8!important}
[data-testid="stSidebar"] .stButton button:hover{background:#4C0DB3!important}
button:focus-visible,input:focus-visible,[role="radio"]:focus-visible{outline:3px solid #B69BF3!important;outline-offset:2px!important}
[data-baseweb="input"]>div,[data-baseweb="select"]>div,[data-baseweb="textarea"]>div{background:#FFFFFF!important;border:1px solid #E5E5EF!important;color:#17142F!important;border-radius:10px!important}
[data-baseweb="input"] input{color:#17142F!important}
[data-testid="stDataFrame"]{border:1px solid #E5E5EF!important;border-radius:15px!important;overflow:hidden;background:#FFFFFF!important}
[data-testid="stSlider"] [role="slider"]{background:#6415D8!important}
[data-testid="stAlert"]{border-radius:12px!important;border-width:1px!important}
[data-testid="stCaptionContainer"],.stCaption{color:#696780!important}
hr{border-color:#DCCBFA!important}\n[data-testid='stExpander']{border:1px solid #E2D4FA!important;border-radius:14px!important;background:#FCFAFF!important}\n[data-testid='stTabs'] button[aria-selected='true']{color:#6415D8!important;border-color:#6415D8!important}
.hero{position:relative;overflow:hidden;background:linear-gradient(112deg,#FFFFFF 8%,#E8D6FF 66%,#CDA8FF 100%);border:1px solid #DCCBFA;border-radius:20px;padding:40px 44px;margin:8px 0 24px}
.hero:after{content:"";position:absolute;pointer-events:none;width:340px;height:340px;border-radius:50%;right:-125px;top:-195px;background:radial-gradient(circle,#A66DF5 0%,#D3B0FF 60%,transparent 72%);opacity:.9}
.hero h1{position:relative;z-index:1;font-size:clamp(2.8rem,5.3vw,4.65rem)!important;line-height:1.07;margin:12px 0 13px;font-weight:800}
.hero p{position:relative;z-index:1;color:#696780;font-size:1rem;margin:0}
.eyebrow{position:relative;z-index:1;font-size:.73rem;color:#6415D8;letter-spacing:.16em;font-weight:800}
.smallprint{font-size:.78rem;color:#696780}
@media(max-width:900px){.block-container{padding:1.25rem 1.1rem 3rem!important}.hero{padding:28px 24px}.hero:after{width:220px;height:220px;right:-110px;top:-120px}}
@media(prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
.ce-prop-line{font-family:'Space Mono',monospace;font-size:1.65rem;font-weight:800;line-height:1.15;margin:.4rem 0 .7rem;color:#2C2443}
.ce-prop-line span{font-size:.77rem;font-weight:500;color:#77758A}
[data-testid="stMetric"]{background:#FFFFFF!important;border:1px solid #E9E8F0!important;box-shadow:none!important;min-height:105px;padding:16px 18px!important}
.stApp,[data-testid="stAppViewContainer"]{background:#F8F8FB!important}
[data-testid="stSidebar"]{background:#5B21B6!important;border-right:1px solid #4C1D95!important}
[data-testid="stSidebar"] label,[data-testid="stSidebar"] p,[data-testid="stSidebar"] span,[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3,[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p{color:#F5F0FF!important}
[data-testid="stSidebar"] .stRadio>div[role="radiogroup"] label:hover{background:#7041C5!important}
[data-testid="stSidebar"] .stRadio>div[role="radiogroup"] label:has(input:checked){background:#FFFFFF!important;color:#4C1D95!important}
[data-testid="stSidebar"] .stRadio>div[role="radiogroup"] label:has(input:checked) p{color:#4C1D95!important}
[data-testid="stSidebar"] .stButton button{background:#FFFFFF!important;color:#4C1D95!important;border-color:#FFFFFF!important}
[data-testid="stSidebar"] .stButton button:hover{background:#F1EAFE!important;color:#4C1D95!important}
[data-testid="stSidebar"] hr{border-color:#8B65D0!important}
.hero{background:linear-gradient(110deg,#FFFFFF 25%,#F3EEFC 100%);border-color:#EAE6F2;padding:30px 36px}
.hero:after{opacity:.14}
.hero h1{font-size:clamp(2.1rem,4vw,3.35rem)!important}
hr{border-color:#EBEAF1!important}
/* Lato for reading; Space Mono for data, numbers and display elements. */
[data-testid="stMetricValue"],[data-testid="stMetricDelta"],[data-testid="stDataFrame"] [role="gridcell"],.ce-prop-line{font-family:'Space Mono',monospace!important}
/* Propified homepage visual system */
.pf-brand{font-family:'Lato',sans-serif;font-size:1.8rem;font-weight:900;letter-spacing:-.05em;color:#260B45;white-space:nowrap}
.pf-bars{color:#8010F5;letter-spacing:-.12em;margin-right:.35em}
.pf-divider{color:#260B45;margin-right:.35em;font-weight:300}
.pf-home-hero{position:relative;overflow:hidden;min-height:270px;display:flex;flex-direction:column;justify-content:center;align-items:center;background:linear-gradient(112deg,#5A079F 0%,#E4D0FA 24%,#FFFFFF 39%,#FFFFFF 63%,#DFCBF7 79%,#350056 100%);border-radius:18px;border:1px solid #E7DDF4;margin:12px 0 24px}
.pf-home-hero:before,.pf-home-hero:after{content:"";position:absolute;width:17%;height:150%;transform:skewX(-30deg);top:-25%;background:rgba(68,0,113,.28)}
.pf-home-hero:before{left:2%}.pf-home-hero:after{right:2%}
.pf-home-logo{z-index:1;color:#29094C;font-family:'Lato',sans-serif;font-size:clamp(2.8rem,7vw,6rem);font-weight:900;letter-spacing:-.06em;white-space:nowrap}
.pf-home-tag{z-index:1;color:#34144F;font-size:.78rem;letter-spacing:.28em;font-weight:900;text-align:center}
.pf-section-space{height:4px}
.pf-sport-label{font-size:.85rem;font-weight:900;letter-spacing:.1em;color:#5D2D9C;margin:10px 0}
@media(max-width:900px){.pf-home-hero{min-height:190px}.pf-home-logo{font-size:2.3rem}.pf-home-tag{font-size:.56rem;letter-spacing:.12em}.pf-brand{font-size:1.25rem}}
/* Responsive layout: wide desktop, comfortable tablet, single-column mobile. */
[data-testid="stVerticalBlock"]{min-width:0}
@media(min-width:901px){[class*="st-key-pf_mobile_nav"]{display:none!important}}
@media(max-width:900px){
  .block-container{padding:1.1rem .9rem 4rem!important;max-width:100%!important}
  /* Hide only the desktop navigation row, never the page content. */
  [data-testid="stHorizontalBlock"]:has(.pf-brand){display:none!important}
  [class*="st-key-pf_mobile_nav"]{display:block!important;background:#FFFFFF;border:1px solid #E9E5F2;border-radius:16px;padding:12px 14px;margin:0 0 16px}
  .pf-mobile-brand{font-family:'Lato',sans-serif;font-size:1.55rem;font-weight:900;color:#35105B;margin-bottom:8px}
  .pf-mobile-brand:first-letter{color:#7C3AED}
  [class*="st-key-pf_mobile_nav"] [data-baseweb="select"]{min-width:0}
  .pf-home-hero{min-height:190px;margin:4px 0 14px;border-radius:14px}
  .hero{padding:22px 18px!important}
  .hero h1{font-size:clamp(1.8rem,7vw,2.6rem)!important}
  [data-testid="stMetric"]{min-height:94px!important;padding:13px!important;border-radius:13px!important}
  [data-testid="stMetricValue"]{font-size:clamp(1.1rem,4.6vw,1.65rem)!important}
  [data-testid="stMetricLabel"]{font-size:.7rem!important}
  .ce-prop-line{font-size:1.35rem}
  [data-testid="stDataFrame"]{max-width:100%;overflow:auto}
  .stRadio [role="radiogroup"]{flex-wrap:wrap!important}
}
@media(max-width:520px){
  /* Streamlit stacks columns automatically; keep enough room for numbers. */
  .pf-home-logo{font-size:clamp(1.95rem,9vw,2.6rem)}
  .pf-home-tag{padding:0 12px;line-height:1.7}
  .block-container{padding-left:.7rem!important;padding-right:.7rem!important}
  [data-testid="stMetricValue"]{overflow-wrap:anywhere}
  [data-testid="stHorizontalBlock"]{gap:.65rem!important}
  [data-testid="stColumn"]{min-width:0!important}
  .stButton button{min-height:42px}
}
</style>""",unsafe_allow_html=True)

def norm(v):
    v=unicodedata.normalize('NFKD',str(v).casefold())
    return ''.join(x for x in v if x.isalnum() and not unicodedata.combining(x))

@st.cache_data(show_spinner=False)
def load_csv(path,mtime):return pd.read_csv(path)
def read_file(filename):
    path=ROOT/filename
    if not path.exists():return None
    try:return load_csv(str(path),path.stat().st_mtime)
    except Exception:return None

def injury_report(sport):
    """Return current injury records and feed diagnostics without guessing health."""
    data=read_file(f'{sport.lower()}_injuries.csv')
    if data is None or data.empty:
        return {}, None, 'No injury file found or the file is empty.'
    required={'Player','Status','CheckedAt'}
    if not required.issubset(data.columns):
        return {}, None, 'Injury file is missing: '+', '.join(sorted(required-set(data.columns)))
    data=data.copy()
    data['CheckedAt']=pd.to_datetime(data['CheckedAt'],utc=True,errors='coerce')
    data['Status']=data['Status'].fillna('REVIEW').astype(str).str.strip().str.upper()
    data['key']=data['Player'].map(norm)
    valid=data.dropna(subset=['CheckedAt'])
    if valid.empty:
        return {}, data, 'Injury file has no valid timestamps.'
    latest=valid['CheckedAt'].max()
    age=pd.Timestamp.now(tz='UTC')-latest
    # Check the actual newest report rather than treating every older record as current.
    if age > pd.Timedelta(hours=12):
        return {}, data, f'Injury report is stale (last checked {latest.strftime("%b %d, %I:%M %p UTC")}). Run refresh_all.py.'
    fresh=valid[valid['CheckedAt']>=pd.Timestamp.now(tz='UTC')-pd.Timedelta(hours=12)].copy()
    fresh=fresh[fresh['key'].ne('')]
    # Conflicting reports for the same name are never silently resolved.
    conflicts=fresh.groupby('key')['Status'].nunique()
    safe=fresh[fresh['key'].map(conflicts).eq(1)].sort_values('CheckedAt').drop_duplicates('key',keep='last')
    lookup=safe.set_index('key')['Status'].to_dict()
    message=f'{len(fresh)} fresh reports; {len(lookup)} unique player statuses; last checked {latest.strftime("%b %d, %I:%M %p UTC")}.'
    return lookup, fresh, message

def modified(filename):
    path=ROOT/filename
    return datetime.fromtimestamp(path.stat().st_mtime).strftime('%b %d, %I:%M %p') if path.exists() else 'Not yet generated'

@st.cache_data(show_spinner=False)
def nba_player_ids():
    try:
        from nba_api.stats.static import players
        return {norm(p['full_name']):p['id'] for p in players.get_players()}
    except Exception as exc:
        st.session_state['nba_photo_error'] = f'{type(exc).__name__}: {exc}'
        return {}

@st.cache_data(show_spinner=False)
def nfl_headshots():
    try:
        import nflreadpy as nfl
        roster=nfl.load_rosters([2026]).to_pandas()
        name_col=next((c for c in ['player_name','full_name','player_display_name','player'] if c in roster),None)
        image_col=next((c for c in ['headshot_url','headshot','headshot_href'] if c in roster),None)
        if name_col and image_col:
            return {norm(n):u for n,u in zip(roster[name_col],roster[image_col]) if isinstance(u,str) and u.startswith('https://')}
    except Exception as exc:
        st.session_state['nfl_photo_error'] = f'{type(exc).__name__}: {exc}'
    return {}

def photo(name,sport):
    if sport=='NBA':
        pid=nba_player_ids().get(norm(name))
        return f'https://cdn.nba.com/headshots/nba/latest/1040x760/{pid}.png' if pid else None
    return nfl_headshots().get(norm(name))

# Read-only recent game logs. These never change model projections or saved picks.
@st.cache_data(ttl=1800,show_spinner=False)
@st.cache_data(ttl=3600,show_spinner=False)
def espn_nba_recent_games(player_name):
    """Fallback to ESPN completed NBA box scores when NBA Stats is unavailable."""
    import requests
    from datetime import timedelta
    session=requests.Session()
    session.headers.update({'User-Agent':'Mozilla/5.0 (compatible; Propified/1.0)'})
    base='https://site.api.espn.com/apis/site/v2/sports/basketball/nba'
    found=[]
    seen=set()
    # One scoreboard request covers the recent date window; summaries are requested
    # only for completed games, with bounded timeouts and cached results.
    end=date.today()
    start=end-timedelta(days=32)
    try:
        response=session.get(base+'/scoreboard',params={'dates':start.strftime('%Y%m%d')+'-'+end.strftime('%Y%m%d'),'limit':300},timeout=10)
        response.raise_for_status()
        events=response.json().get('events',[])
    except Exception:
        return pd.DataFrame()
    events=sorted(events,key=lambda e:e.get('date',''),reverse=True)
    for event in events:
        if len(found)>=5:
            break
        competition=(event.get('competitions') or [{}])[0]
        if not competition.get('status',{}).get('type',{}).get('completed',False):
            continue
        event_id=str(event.get('id',''))
        if not event_id or event_id in seen:
            continue
        seen.add(event_id)
        try:
            response=session.get(base+'/summary',params={'event':event_id},timeout=8)
            response.raise_for_status()
            box=response.json().get('boxscore',{})
        except Exception:
            continue
        for team in box.get('players',[]):
            for group in team.get('statistics',[]):
                labels=group.get('labels',[])
                names=group.get('names',[])
                for entry in group.get('athletes',[]):
                    athlete=entry.get('athlete',{})
                    if norm(athlete.get('displayName',''))!=norm(player_name):
                        continue
                    if entry.get('didNotPlay',False):
                        continue
                    stats=dict(zip(names or labels,entry.get('stats',[])))
                    def number(*keys):
                        for key in keys:
                            val=stats.get(key)
                            if val is not None:
                                try:return float(val)
                                except (TypeError,ValueError):pass
                        return None
                    # ESPN's box score labels are stable for the core counting stats.
                    points=number('PTS','points')
                    rebounds=number('REB','rebounds')
                    assists=number('AST','assists')
                    threes=number('3PT','threePointFieldGoalsMade')
                    if isinstance(stats.get('3PT'),str) and '-' in stats['3PT']:
                        try:threes=float(stats['3PT'].split('-')[0])
                        except ValueError:threes=None
                    if points is None:
                        continue
                    found.append({'Game':str(event.get('date',''))[:10],'Points':points,'Rebounds':rebounds,'Assists':assists,'Threes':threes})
                    break
                if found and found[-1]['Game']==str(event.get('date',''))[:10]:break
            if found and found[-1]['Game']==str(event.get('date',''))[:10]:break
    return pd.DataFrame(found[::-1])
@st.cache_data(ttl=1800,show_spinner=False)
def recent_game_logs(sport, player_name, player_id=None):
    if sport == 'NFL':
        import nflreadpy as nfl
        try:
            raw=nfl.load_player_stats([2025,2026],summary_level='week').to_pandas()
        except Exception:
            raw=nfl.load_player_stats([2025],summary_level='week').to_pandas()
        name_col=next((c for c in ['player_name','player_display_name','player'] if c in raw),None)
        id_col=next((c for c in ['player_id','gsis_id'] if c in raw),None)
        if name_col is None:raise ValueError('NFL weekly stats missing player names')
        if player_id and id_col:
            rows=raw[raw[id_col].astype(str).eq(str(player_id))].copy()
        else:
            rows=raw[raw[name_col].map(norm).eq(norm(player_name))].copy()
        if 'season_type' in rows:
            rows=rows[rows['season_type'].astype(str).str.upper().isin(['REG','REGULAR'])]
        for key in ['season','week']:
            rows[key]=pd.to_numeric(rows[key],errors='coerce')
        rows=rows.dropna(subset=['season','week']).sort_values(['season','week']).tail(5)
        mapping={'Passing Yards':'passing_yards','Rushing Yards':'rushing_yards',
                 'Receiving Yards':'receiving_yards','Receptions':'receptions',
                 'Passing TDs':'passing_tds','Receiving TDs':'receiving_tds',
                 'Interceptions':'passing_interceptions','Rushing Attempts':'carries'}
        result=pd.DataFrame({'Game':[f"{int(r.season)} W{int(r.week)}" for r in rows.itertuples(index=False)]})
        for label,field in mapping.items():
            if field in rows:
                result[label]=pd.to_numeric(rows[field],errors='coerce').to_numpy()
        return result
    # NBA IDs from nba_api are NBA Stats IDs, not ESPN IDs.
    # Fetch actual box-score game logs from the matching NBA Stats endpoint.
    from nba_api.stats.endpoints import playergamelog
    pid=nba_player_ids().get(norm(player_name))
    if not pid:
        return espn_nba_recent_games(player_name)
    today=datetime.now()
    season_year=today.year if today.month>=10 else today.year-1
    games=[]
    fetch_errors=[]
    for year in [season_year,season_year-1]:
        season=f'{year}-{str((year+1)%100).zfill(2)}'
        try:
            raw=playergamelog.PlayerGameLog(player_id=int(pid),season=season,
                                            season_type_all_star='Regular Season',
                                            timeout=12).get_data_frames()[0]
        except Exception as exc:
            fetch_errors.append(f'{season}: {type(exc).__name__}: {str(exc)[:120]}')
            continue
        if not raw.empty:
            games.append(raw)
        if sum(len(g) for g in games)>=5:
            break
    if not games:
        return espn_nba_recent_games(player_name)
    data=pd.concat(games,ignore_index=True)
    if not {'GAME_DATE','PTS','REB','AST','FG3M'}.issubset(data.columns):
        return espn_nba_recent_games(player_name)
    data['GAME_DATE']=pd.to_datetime(data['GAME_DATE'],errors='coerce')
    data=data.dropna(subset=['GAME_DATE']).sort_values('GAME_DATE').tail(5)
    return pd.DataFrame({
        'Game':data['GAME_DATE'].dt.strftime('%b %d').to_numpy(),
        'Points':pd.to_numeric(data['PTS'],errors='coerce').to_numpy(),
        'Rebounds':pd.to_numeric(data['REB'],errors='coerce').to_numpy(),
        'Assists':pd.to_numeric(data['AST'],errors='coerce').to_numpy(),
        'Threes':pd.to_numeric(data['FG3M'],errors='coerce').to_numpy()
    })

def show_recent_games(sport, player_name, stat=None, player_id=None):
    st.markdown('#### Last 5 games')
    try:
        logs=recent_game_logs(sport,player_name,player_id)
    except Exception as exc:
        st.warning(f'Recent game logs unavailable: {type(exc).__name__}: {str(exc)[:240]}')
        return
    if logs.empty or len(logs.columns)<2:
        st.info('Verified per-game stats are not available for this player yet.')
        return
    choices=[c for c in logs.columns if c!='Game']
    aliases={'PTS':'Points','REB':'Rebounds','AST':'Assists','3PM':'Threes',
             '3PT':'Threes','3-Pointers Made':'Threes','Passing Yds':'Passing Yards',
             'Receiving Yds':'Receiving Yards','Rushing Yds':'Rushing Yards'}
    preferred=aliases.get(str(stat),stat)
    default=choices.index(preferred) if preferred in choices else 0
    selected=st.selectbox('Stat to chart',choices,index=default,key=f'log_stat_{sport}_{norm(player_name)}_{norm(stat)}')
    chart=logs[['Game',selected]].dropna().set_index('Game')
    if chart.empty:
        st.info('No completed games with this statistic.')
        return
    values=chart[selected]
    k1,k2,k3=st.columns(3)
    k1.metric('Last 5 average',f'{values.mean():.1f}',help='Average from the completed games shown below.')
    k2.metric('Highest game',f'{values.max():.1f}')
    k3.metric('Lowest game',f'{values.min():.1f}')
    st.bar_chart(chart,color='#7C3AED',use_container_width=True)
    st.caption(f'{len(chart)} completed games · Each purple bar represents one real game, not a prediction.')
    with st.expander('See the exact game-by-game numbers'):
        st.dataframe(logs,hide_index=True,use_container_width=True)

SPORT_FILES={'NBA':{'comparison':'nba_prizepicks_comparison.csv','projections':'todays_nba_projections.csv','lines':'prizepicks_nba_lines.csv'},
             'NFL':{'comparison':'nfl_comparison.csv','projections':'nfl_projections.csv','lines':'nfl_prizepicks_lines.csv'}}
def navigate_to(target, selected_sport=None):
    st.session_state['propified_page']=target
    if selected_sport is not None:
        st.session_state['propified_sport']=selected_sport

with st.sidebar:
    st.markdown('### ◉ **PROPIFIED**')
    st.caption('THE PERFORMANCE LAB')
    st.divider()
    sport=st.radio('SPORT',['NBA','NFL'],horizontal=True,key='propified_sport')
    nav_icons={'Overview':'⌂','Betting Comparisons':'⇄','All PrizePicks Props':'▦','Player Props':'♙','Lay of the Day':'✦','Model History':'◷','Model Performance':'▥','Settings':'⚙'}
    page=st.radio('NAVIGATION',list(nav_icons),format_func=lambda name:f"{nav_icons[name]}   {name}",label_visibility='collapsed',key='propified_page')
    st.divider()
    if st.button('↻ Refresh data',type='primary',use_container_width=True):
        st.cache_data.clear();st.rerun()
    st.caption('Hosted data · Propified repository')

def standard_prizepicks_props(selected_sport):
    """Display all available standard, non-live, non-combo, non-promo PrizePicks lines.
    Unmatched markets remain visible; they are not invented projections.
    """
    if selected_sport=='NBA':
        raw=read_file('prizepicks_nba_lines.csv')
        if raw is None or raw.empty:return pd.DataFrame()
        required={'playerName','stat','line','oddsType'}
        if not required.issubset(raw.columns):return pd.DataFrame()
        data=raw.copy()
        data=data[data['oddsType'].astype(str).str.casefold().eq('standard')]
        if 'projectionType' in data.columns:
            data=data[data['projectionType'].astype(str).str.upper().eq('STANDARD')]
        for flag in ['isLive','isCombo','isPromo']:
            if flag in data.columns:
                data=data[data[flag].astype(str).str.casefold().isin(['false','0'])]
        if 'league' in data.columns:
            data=data[data['league'].astype(str).str.upper().eq('NBA')]
        data=data.rename(columns={'playerName':'Player','team':'Team','stat':'Stat','line':'Line','gameStartsAt':'GameStartsAt'})
    else:
        raw=read_file('nfl_prizepicks_all_standard.csv')
        if raw is None or raw.empty:
            raw=read_file('nfl_prizepicks_lines.csv')
        if raw is None or raw.empty:return pd.DataFrame()
        data=raw.copy().rename(columns={'SportsbookLine':'Line'})
    if not {'Player','Stat','Line'}.issubset(data.columns):return pd.DataFrame()
    data['Line']=pd.to_numeric(data['Line'],errors='coerce')
    data=data.dropna(subset=['Player','Stat','Line']).copy()
    if 'GameStartsAt' in data.columns:
        starts=pd.to_datetime(data['GameStartsAt'],utc=True,errors='coerce')
        data=data.loc[starts.notna() & (starts>pd.Timestamp.now(tz='UTC'))].copy()
    data['Team']=data.get('Team','')
    return data.drop_duplicates(subset=['Player','Stat','Line','GameStartsAt'] if 'GameStartsAt' in data.columns else ['Player','Stat','Line'])


@st.cache_data(ttl=300,show_spinner=False)
def nfl_live_feed():
    from prizepicks_partner_api import fetch
    return fetch('NFL',persist=False)

def nfl_allowed_lines(data):
    from nfl_compare import clean
    excluded={'playerfantasypoints','fantasypoints','playerlongestreception',
              'longestreception','playerlongestrush','longestrush',
              'playertacklesplusast','tacklesplusassists','totaltacklesassists'}
    result=data.copy()
    market=result['MarketKey'] if 'MarketKey' in result else result['Stat']
    result=result.loc[~(market.fillna('').map(clean).isin(excluded) |
                        result['Stat'].fillna('').map(clean).isin(excluded))].copy()
    result['Line']=pd.to_numeric(result['Line'],errors='coerce')
    result=result.dropna(subset=['Player','Stat','Line'])
    if 'GameStartsAt' in result:
        starts=pd.to_datetime(result['GameStartsAt'],utc=True,errors='coerce')
        result=result.loc[starts.notna() & starts.gt(pd.Timestamp.now(tz='UTC'))].copy()
    return result.drop_duplicates(['Player','Stat','Line'])

files=SPORT_FILES[sport]
comparison=read_file(files['comparison'])
projections=read_file(files['projections'])
nfl_board_source=None
nfl_board_lines=0
if sport=='NFL' and page in ('Betting Comparisons','Overview','Lay of the Day'):
    # Never silently show an old 161-row CSV when the live feed fails.
    from nfl_compare import match_frames
    try:
        current_lines=nfl_allowed_lines(nfl_live_feed())
        nfl_board_source='Live PrizePicks'
    except Exception as exc:
        st.warning(f'Live NFL feed unavailable ({type(exc).__name__}: {exc}). Recalculating from saved standard lines instead.')
        current_lines=nfl_allowed_lines(standard_prizepicks_props('NFL'))
        nfl_board_source='Saved PrizePicks (live unavailable)'
    nfl_board_lines=len(current_lines)
    if projections is not None and not projections.empty and not current_lines.empty:
        try:
            comparison=match_frames(projections,current_lines.rename(columns={'Line':'SportsbookLine'}))
        except Exception as exc:
            comparison=pd.DataFrame()
            st.error(f'NFL matching failed: {type(exc).__name__}: {exc}')
    else:
        comparison=pd.DataFrame()
        st.warning('NFL projection data or current standard lines unavailable.')
    st.caption(f'NFL comparison source: {nfl_board_source} · {nfl_board_lines} eligible lines · {len(comparison)} matched before time filtering.')
saved_comparison= comparison.copy() if comparison is not None else pd.DataFrame()
if comparison is not None and not comparison.empty:
    required=['Player','Team','Stat','PrizePicksLine','ModelProjection','Difference']
    missing=set(required)-set(comparison.columns)
    if missing:
        st.error('Comparison CSV is missing: '+', '.join(sorted(missing)));st.stop()
    for c in ['PrizePicksLine','ModelProjection','Difference']:
        comparison[c]=pd.to_numeric(comparison[c],errors='coerce')
    comparison=comparison.dropna(subset=['PrizePicksLine','ModelProjection','Difference']).copy()
    # Keep historical CSVs intact; hide props once their scheduled game starts.
    # Unknown or invalid tipoff times are excluded rather than treated as live picks.
    if 'GameStartsAt' in comparison.columns:
        starts=pd.to_datetime(comparison['GameStartsAt'],utc=True,errors='coerce')
        now_utc=pd.Timestamp.now(tz='UTC')
        removed=int((starts.isna() | (starts<=now_utc)).sum())
        comparison=comparison.loc[starts.notna() & (starts>now_utc)].copy()
        if removed:
            st.sidebar.caption(f'{removed} started/unscheduled props hidden from live board')
    else:
        st.sidebar.warning('Missing game start times: live betting board hidden for safety.')
        comparison=comparison.iloc[0:0].copy()
    comparison['Gap']=comparison['Difference'].abs()
    comparison['Model lean']=comparison['Difference'].map(lambda x:'OVER' if x>0 else 'UNDER' if x<0 else 'EVEN')
    comparison['Headshot']=comparison['Player'].map(lambda n:photo(n,sport))
    injury_lookup, injury_records, injury_message=injury_report(sport)
    comparison['Injury status']=comparison['Player'].map(lambda n:injury_lookup.get(norm(n),'UNVERIFIED'))
else:comparison=pd.DataFrame(columns=['Player','Team','Stat','PrizePicksLine','ModelProjection','Difference','Gap','Model lean','Headshot','Injury status'])

# Top navigation mirrors the sidebar without changing the existing analytics routes.
# Desktop and mobile navigation use the same page state and underlying data.
navcols=st.columns([2.6,1,1,1.35,1,1.15,1.5],vertical_alignment='center')
with navcols[0]:
    st.markdown('<div class="pf-brand"><span class="pf-bars">▂▅▇</span><span class="pf-divider">│</span>Propified</div>',unsafe_allow_html=True)
for slot,label,target in [(1,'Home','Overview'),(2,'Props','All PrizePicks Props'),(3,'Comparisons','Betting Comparisons'),(4,'Results','Model History'),(5,'Insights','Model Performance')]:
    with navcols[slot]:
        st.button(label,key='topnav_'+target,use_container_width=True,type='primary' if page==target else 'secondary',on_click=navigate_to,args=(target,))
with navcols[6]:
    if st.button('↻ Refresh Data',key='topnav_refresh',use_container_width=True):
        st.cache_data.clear()
        st.rerun()
# Compact mobile navigation: full-width brand + single page selector.
with st.container(key='pf_mobile_nav'):
    st.markdown('<div class="pf-mobile-brand">▂▅▇ <strong>Propified</strong></div>',unsafe_allow_html=True)
    mobile_pages={'Home':'Overview','Props':'All PrizePicks Props','Compare':'Betting Comparisons','Results':'Model History','Insights':'Model Performance','Players':'Player Props','Lay of the Day':'Lay of the Day','Settings':'Settings'}
    def on_mobile_page_change():
        selected=st.session_state.get('pf_mobile_page_choice','Home')
        st.session_state['propified_page']=mobile_pages.get(selected,'Overview')
    current_mobile_page=next((label for label,target in mobile_pages.items() if target==page),'Home')
    if st.session_state.get('pf_mobile_page_choice')!=current_mobile_page:
        st.session_state['pf_mobile_page_choice']=current_mobile_page
    st.selectbox('Go to',list(mobile_pages),key='pf_mobile_page_choice',on_change=on_mobile_page_change)

if page!='Overview':
    st.markdown(f'''<div class="hero"><span class="eyebrow">◉ PROPIFIED / {sport} ANALYTICS</span>
    <h1>Find Your <span style="color:#6415D8">Edge.</span></h1>
    <p>Player projections. Sportsbook lines. A clearer picture of the game.</p></div>''',unsafe_allow_html=True)

st.caption(f"{date.today():%A, %B %d, %Y}  ·  {sport} comparison file: {modified(files['comparison'])}")
st.caption('Updated file timestamps do not verify that games, line availability, or player status are current.')
st.caption(f"Injury feed: {modified(f'{sport.lower()}_injuries.csv')} · UNVERIFIED means no fresh matched report, not healthy.")
if not comparison.empty:
    st.caption(f'Injury diagnostics: {injury_message}')
    matched=comparison.loc[comparison['Injury status'].ne('UNVERIFIED'),'Player'].nunique()
    total=comparison['Player'].nunique()
    with st.expander(f'Injury scout details · {matched}/{total} comparison players have a matched report'):
        st.caption('Injury feeds typically list reported injuries, not every healthy player. UNVERIFIED does not mean OUT or healthy. REVIEW is a feed status requiring confirmation.')
        if injury_records is not None and not injury_records.empty:
            show=[c for c in ['Player','Team','Status','Detail','CheckedAt','Source'] if c in injury_records.columns]
            st.dataframe(injury_records[show],hide_index=True,use_container_width=True)
        else:
            st.warning(injury_message)



NBA_MARKET_LABELS={
    'player_pts_rebs':'Points + Rebounds',
    'player_pts_asts':'Points + Assists',
    'player_rebs_asts':'Rebounds + Assists',
    'player_pts_rebs_asts':'Points + Rebounds + Assists',
    'player_blks_stls':'Steals + Blocks',
    'player_stls_blks':'Steals + Blocks',
    'player_fg_attempts':'Field Goals Attempted',
    'player_fg_made':'Field Goals Made',
    'player_ft_attempts':'Free Throws Attempted',
    'player_ft_made':'Free Throws Made',
    '3-PT Made':'Threes','player_points':'Points','player_rebounds':'Rebounds',
    'player_assists':'Assists','player_threes':'Threes','player_three_pointers':'Threes',
    'player_steals':'Steals','player_blocks':'Blocks','player_turnovers':'Turnovers',
    'player_points_rebounds':'Points + Rebounds',
    'player_points_assists':'Points + Assists',
    'player_rebounds_assists':'Rebounds + Assists',
    'player_points_rebounds_assists':'Points + Rebounds + Assists',
    'player_steals_blocks':'Steals + Blocks',
    'player_field_goals_attempted':'Field Goals Attempted',
    'player_field_goals_made':'Field Goals Made',
    'player_free_throws_attempted':'Free Throws Attempted',
    'player_free_throws_made':'Free Throws Made',
}

def coverage_audit(lines, model, matched_comparisons, selected_sport):
    """Account for every feed row; do not equate an unsupported market with a bad prediction."""
    out=lines.copy()
    out['ModelStat']=out['Stat'].astype(str).map(
        lambda x: NBA_MARKET_LABELS.get(x,x) if selected_sport=='NBA' else x)
    if selected_sport=='NBA':
        supported=set(model.columns)-{'Player','Team','Games','Method'} if model is not None else set()
    else:
        supported=set(model['Stat'].dropna().astype(str)) if model is not None and 'Stat' in model else set()
    model_names=set(model['Player'].map(norm)) if model is not None and 'Player' in model else set()
    if selected_sport=='NFL' and model is not None and 'Player' in model:
        from nfl_compare import short_key
        model_short_names=set(model['Player'].map(short_key))
    else:
        model_short_names=set()
    if matched_comparisons is not None and not matched_comparisons.empty:
        comparison_keys=set(zip(matched_comparisons['Player'].map(norm),
                                matched_comparisons['Stat'].map(norm),
                                pd.to_numeric(matched_comparisons['PrizePicksLine'],errors='coerce').round(3)))
    else:
        comparison_keys=set()
    out['Has model projection']=[
        (norm(r.Player),norm(r.ModelStat),round(float(r.Line),3)) in comparison_keys
        for r in out.itertuples(index=False)]
    def reason(row):
        if row['Has model projection']:return 'Compared'
        if row['ModelStat'] not in supported:return 'Stat not modeled'
        if norm(row['Player']) not in model_names and not (selected_sport=='NFL' and short_key(row['Player']) in model_short_names):return 'Player missing from model'
        return 'Identity, team, or stat mismatch (or saved comparison is stale)'
    out['Coverage status']=out.apply(reason,axis=1)
    return out

if page=='All PrizePicks Props':
    st.subheader(f'{sport} PrizePicks props')
    st.caption('Standard, non-live, single-player lines only. A missing line is never fabricated.')
    search=st.text_input('Find a player',placeholder='Search Jordan Addison, Justin Jefferson...',key=f'props_search_{sport}')
    source=st.radio('Data source',['Live PrizePicks feed','Saved feed'],horizontal=True,key=f'props_source_v2_{sport}')
    all_props=pd.DataFrame()
    feed_note=''
    if source.startswith('Live'):
        try:
            from prizepicks_partner_api import fetch
            with st.spinner('Loading live standard props...'):
                all_props=nfl_live_feed() if sport=='NFL' else fetch(sport,persist=False)
            feed_note=f'Live feed: {len(all_props)} lines'
        except Exception as exc:
            st.warning(f'Live feed unavailable ({type(exc).__name__}). Showing saved data instead.')
            all_props=standard_prizepicks_props(sport)
            feed_note='Saved fallback'
    else:
        all_props=standard_prizepicks_props(sport)
        feed_note='Saved feed'
    if all_props is None or all_props.empty:
        st.warning('No props returned. Try the other data source.')
        st.stop()
    all_props=all_props.copy()
    if sport=='NFL':
        # Exclude these unsupported NFL markets from both the displayed feed
        # and its coverage denominator, regardless of source or label style.
        excluded_nfl_markets={
            'playerfantasypoints','fantasypoints',
            'playerlongestreception','longestreception',
            'playerlongestrush','longestrush',
            'playertacklesplusast','tacklesplusassists',
            'totaltacklesassists',
        }
        market_names=all_props['MarketKey'] if 'MarketKey' in all_props else all_props['Stat']
        normalized_markets=market_names.fillna('').astype(str).map(norm)
        normalized_stats=all_props['Stat'].fillna('').astype(str).map(norm)
        excluded=normalized_markets.isin(excluded_nfl_markets) | normalized_stats.isin(excluded_nfl_markets)
        removed=int(excluded.sum())
        all_props=all_props.loc[~excluded].copy()
        st.caption(f'{removed} excluded NFL lines: fantasy points, longest reception, longest rush, tackles + assists.')
    all_props['Line']=pd.to_numeric(all_props['Line'],errors='coerce')
    all_props=all_props.dropna(subset=['Player','Stat','Line'])
    if 'GameStartsAt' in all_props:
        starts=pd.to_datetime(all_props['GameStartsAt'],utc=True,errors='coerce')
        all_props=all_props.loc[starts.notna() & starts.gt(pd.Timestamp.now(tz='UTC'))].copy()
    all_props=all_props.drop_duplicates(subset=['Player','Stat','Line'])
    if sport=='NFL':
        from nfl_compare import match_frames, short_key
        try:
            if projections is not None and not projections.empty:
                live_comparisons=match_frames(projections,all_props.rename(columns={'Line':'SportsbookLine'}))
            else:
                live_comparisons=pd.DataFrame()
        except Exception as exc:
            live_comparisons=pd.DataFrame()
            st.warning(f'Matching error: {type(exc).__name__}. Props remain visible.')
        if not live_comparisons.empty:
            from nfl_compare import clean
            nfl_stat_aliases={
                'playerrectargets':'Targets','rectargets':'Targets',
                'playerreceivingyards':'Receiving Yards',
                'playerreceptions':'Receptions',
                'playerpassyds':'Passing Yards',
                'playerpassattempts':'Passing Attempts',
                'playerpasscompletions':'Passing Completions',
                'playerrushyards':'Rushing Yards',
                'playerrushattempts':'Rushing Attempts',
                'playerint':'Interceptions','playerpasstds':'Passing TDs',
                'playerrushtds':'Rushing TDs',
                'playercompletionpercentage':'Completion Percentage',
                'playerrushyardspercarry':'Yards Per Rush Attempt',
                'playerpassplusrushyds':'Passing + Rushing Yards',
                'playerrushplusrecyds':'Rushing + Receiving Yards',
            }
            matched=live_comparisons.copy()
            matched['_match_key']=list(zip(
                matched['Player'].map(norm),
                matched['Stat'].map(lambda x:clean(nfl_stat_aliases.get(clean(x),x))),
                pd.to_numeric(matched['PrizePicksLine'],errors='coerce').round(3)))
            matched=matched.drop_duplicates('_match_key').set_index('_match_key')
            all_props['_match_key']=list(zip(
                all_props['Player'].map(norm),
                all_props['Stat'].map(lambda x:clean(nfl_stat_aliases.get(clean(x),x))),
                pd.to_numeric(all_props['Line'],errors='coerce').round(3)))
            all_props['Has model projection']=all_props['_match_key'].isin(matched.index)
            all_props['ModelProjection']=pd.to_numeric(
                all_props['_match_key'].map(matched['ModelProjection']),errors='coerce')
            all_props['Difference']=(all_props['ModelProjection']-all_props['Line']).round(2)
            all_props=all_props.drop(columns=['_match_key'])
        else:
            all_props['Has model projection']=False
            all_props['ModelProjection']=float('nan')
            all_props['Difference']=float('nan')
    else:
        # Compare each live NBA line directly to the matching model column.
        # Missing player or unmodeled stat stays visible without a fabricated value.
        all_props['ModelStat']=all_props['Stat'].map(lambda x:NBA_MARKET_LABELS.get(x,x))
        all_props['ModelProjection']=float('nan')
        if projections is not None and not projections.empty and 'Player' in projections:
            model=projections.copy()
            model['_key']=model['Player'].map(norm)
            unique=model['_key'].value_counts()
            model=model[model['_key'].map(unique).eq(1)].set_index('_key')
            for stat in all_props['ModelStat'].dropna().unique():
                if stat not in model.columns:
                    continue
                mask=all_props['ModelStat'].eq(stat)
                all_props.loc[mask,'ModelProjection']=pd.to_numeric(
                    all_props.loc[mask,'Player'].map(lambda name:model[stat].get(norm(name))),errors='coerce').to_numpy()
        all_props['Has model projection']=all_props['ModelProjection'].notna()
        all_props['Difference']=(all_props['ModelProjection']-all_props['Line']).round(2)
    all_props['Has model projection']=all_props['Has model projection'].fillna(False).astype(bool)
    if sport=='NFL':
        # Coverage must distinguish unsupported markets from identity failures.
        from nfl_compare import clean, short_key
        nfl_aliases={
            'playerpassyds':'Passing Yards','playerpassattempts':'Passing Attempts',
            'playerpasscompletions':'Passing Completions','playerrushyards':'Rushing Yards',
            'playerrushattempts':'Rushing Attempts','playerreceivingyards':'Receiving Yards',
            'playerreceptions':'Receptions','playerrectargets':'Targets',
            'playerint':'Interceptions','playerpasstds':'Passing TDs',
            'playerrushtds':'Rushing TDs','playercompletionpercentage':'Completion Percentage',
            'playerrushyardspercarry':'Yards Per Rush Attempt',
            'playerpassplusrushyds':'Passing + Rushing Yards',
            'playerrushplusrecyds':'Rushing + Receiving Yards',
        }
        all_props['ModelStat']=all_props['Stat'].map(lambda x:nfl_aliases.get(clean(x),x))
        model_stats=set(projections['Stat'].dropna().astype(str)) if projections is not None and not projections.empty and 'Stat' in projections else set()
        model_players=set(projections['Player'].map(short_key)) if projections is not None and not projections.empty and 'Player' in projections else set()
        def missing_reason(row):
            if row['Has model projection']:return 'Matched'
            if row['ModelStat'] not in model_stats:return 'Market not in current projections'
            if short_key(row['Player']) not in model_players:return 'Player not in current projections'
            return 'Player/stat match failed'
        all_props['Coverage reason']=all_props.apply(missing_reason,axis=1)
        with st.expander('Why are NFL props unmatched?',expanded=False):
            counts=all_props['Coverage reason'].value_counts().rename_axis('Reason').reset_index(name='Props')
            st.dataframe(counts,hide_index=True,use_container_width=True)
            market_summary=all_props.groupby(['Stat','Coverage reason']).size().reset_index(name='Props')
            st.dataframe(market_summary.sort_values('Props',ascending=False),hide_index=True,use_container_width=True)
    if sport=='NFL' and search and 'addison' in search.casefold():
        addison_lines=all_props[all_props['Player'].astype(str).str.contains('Addison',case=False,na=False)]
        if addison_lines.empty:
            st.info('Jordan Addison has no eligible upcoming lines in the selected PrizePicks feed.')
        elif not addison_lines['Has model projection'].any():
            model_addison=(projections[projections['Player'].astype(str).str.contains('Addison',case=False,na=False)]
                           if projections is not None and not projections.empty else pd.DataFrame())
            if model_addison.empty:
                st.warning('Jordan Addison is in PrizePicks but missing from the current NFL model projections. Check whether his 2026 weekly game data is present, then refresh the NFL model.')
            else:
                available=', '.join(sorted(model_addison['Stat'].dropna().astype(str).unique()))
                st.warning(f'Jordan Addison is in PrizePicks, but his listed markets did not match a projection. Model stats available: {available or "none"}. Check player ID and market mapping.')
        else:
            st.success(f'Jordan Addison has {int(addison_lines["Has model projection"].sum())} matched props in this feed.')
    st.caption(f'{feed_note} · {len(all_props)} upcoming props · {int(all_props["Has model projection"].sum())} matched')
    market=st.selectbox('Market',['All']+sorted(all_props['Stat'].dropna().astype(str).unique()),key=f'props_market_v2_{sport}')
    coverage=st.selectbox('Show',['All props','Matched only','Unmatched only'],key=f'props_coverage_v2_{sport}')
    view=all_props
    if search:
        view=view[view['Player'].astype(str).str.contains(search,case=False,regex=False,na=False)]
    if market!='All':
        view=view[view['Stat'].eq(market)]
    if coverage=='Matched only':
        view=view[view['Has model projection']]
    elif coverage=='Unmatched only':
        view=view[~view['Has model projection']]
    st.caption(f'{len(view)} matching props')
    display=[c for c in ['Player','Team','Stat','Line','ModelProjection','Difference','GameStartsAt','Has model projection','Coverage reason'] if c in view.columns]
    st.dataframe(view[display],hide_index=True,use_container_width=True)
    if search and view.empty:
        st.info('No matching upcoming standard line in this source. Try the other source; this does not mean the player is missing from the model.')
    if sport=='NFL' and not live_comparisons.empty:
        with st.expander('Matched NFL model projections'):
            shown=live_comparisons
            if search:
                shown=shown[shown['Player'].astype(str).str.contains(search,case=False,regex=False,na=False)]
            st.dataframe(shown[[c for c in ['Player','Team','Stat','PrizePicksLine','ModelProjection','Difference','Direction'] if c in shown.columns]],hide_index=True,use_container_width=True)
    with st.expander('Diagnostics and downloads'):
        st.download_button('Download visible props',view[display].to_csv(index=False).encode(),f'{sport.lower()}_standard_props.csv','text/csv')
        if sport=='NFL' and search:
            saved=standard_prizepicks_props(sport)
            if saved is not None and not saved.empty:
                saved=saved[saved['Player'].astype(str).str.contains(search,case=False,regex=False,na=False)]
                st.caption(f'Saved feed also contains {len(saved)} matching lines for this search.')
                if not saved.empty:
                    st.dataframe(saved[[c for c in ['Player','Stat','Line','GameStartsAt'] if c in saved.columns]],hide_index=True,use_container_width=True)
    st.stop()

if page=='Lay of the Day':
    st.subheader('✦ Lay of the Day · 3-Leg Parlay')
    st.caption('Three different players, three model-selected props. An informational parlay idea, not a verified winning ticket or automatically placed wager.')
    if comparison.empty:
        st.info('No upcoming, time-verified sportsbook comparisons available. No parlay selected.')
        st.stop()
    eligible=comparison.copy()
    # Exclude known injury concerns; an unverified player is shown with a warning.
    eligible=eligible[~eligible['Injury status'].isin(['OUT','DOUBTFUL','QUESTIONABLE','REVIEW'])]
    eligible=eligible[eligible['Difference'].abs().gt(0)].copy()
    if 'PickQuality' in eligible.columns:
        quality=eligible['PickQuality'].fillna('').astype(str).str.upper()
        eligible=eligible[quality.isin(['QUALIFIED','STRONG','HIGH','GOOD','A','A+'])]
    if 'ReliabilityScore' in eligible.columns:
        eligible['ReliabilityScore']=pd.to_numeric(eligible['ReliabilityScore'],errors='coerce')
        eligible=eligible.dropna(subset=['ReliabilityScore'])
        eligible=eligible.sort_values(['ReliabilityScore','Gap'],ascending=False)
    else:
        eligible=eligible.sort_values('Gap',ascending=False)
    # Avoid multiple legs on the same player. Distinct players do not guarantee independence.
    eligible=eligible.drop_duplicates(subset=['Player'])
    if len(eligible)<3:
        st.info(f'Only {len(eligible)} eligible distinct-player props available. A three-leg parlay will not be fabricated.')
        st.stop()
    picks=eligible.head(3)
    st.markdown('#### Today’s three legs')
    st.caption('Ordered by the model’s existing heuristic ranking, not calibrated win probabilities.')
    for i,(_,pick) in enumerate(picks.iterrows(),start=1):
        with st.container(border=True):
            image_col,body=st.columns([1,4],vertical_alignment='center')
            with image_col:
                headshot=pick.get('Headshot')
                if isinstance(headshot,str) and headshot.startswith('https://'):
                    st.image(headshot,use_container_width=True)
                else:
                    st.markdown('### ✦')
            with body:
                st.markdown(f"**LEG {i} · {pick['Player']}**")
                st.caption(f"{pick['Team']} · {pick['Stat']}")
                st.markdown(f"### :violet[{pick['Model lean']} {pick['PrizePicksLine']:.1f}]")
                c1,c2=st.columns(2)
                c1.metric('Model projection',f"{pick['ModelProjection']:.1f}")
                c2.metric('Projection gap',f"{pick['Difference']:+.1f}")
                st.caption('Injury verification: '+str(pick['Injury status']))
                if pick['Injury status']=='UNVERIFIED':
                    st.warning('Availability unverified — check injury and lineup status.')
            with st.expander(f"Last five games · {pick['Player']}"):
                show_recent_games(sport,str(pick['Player']),str(pick['Stat']))
    st.markdown('#### Parlay summary')
    st.dataframe(picks[['Player','Team','Stat','Model lean','PrizePicksLine','ModelProjection','Difference']],
                 hide_index=True,use_container_width=True,
                 column_config={'PrizePicksLine':st.column_config.NumberColumn('Line',format='%.1f'),
                                'ModelProjection':st.column_config.NumberColumn('Projection',format='%.1f'),
                                'Difference':st.column_config.NumberColumn('Gap',format='%+.1f')})
    st.caption('All three legs must win for a standard three-leg parlay to win. No combined hit probability or expected payout is shown without validated leg probabilities, dependency estimates and actual payout terms.')
    st.stop()

if page=='Settings':
    st.subheader(f'{sport} model controls')
    key=f'{sport.lower()}_weight'
    if key not in st.session_state:st.session_state[key]=60
    current=st.slider('Current season weight (preview only)',0,100,st.session_state[key],5)
    a,b=st.columns(2)
    a.metric('Current season',f'{current}%')
    b.metric('Previous season',f'{100-current}%')
    st.warning('Preview only: changing this slider does not recalculate or save the model. Model parameters are controlled by the scheduled pipeline.')
    if False and st.button('Apply Settings & Recalculate',type='primary'):
        model='nba_model.py' if sport=='NBA' else 'nfl_model.py'
        comparator='nba_prizepicks_model.py' if sport=='NBA' else 'nfl_compare.py'
        if not (ROOT/model).exists() or not (ROOT/comparator).exists():
            st.error(f'Missing {model} or {comparator} in Documents.')
        elif not (ROOT/files['lines']).exists():
            st.error(f'Missing {files["lines"]}. Download sportsbook lines first.')
        else:
            with st.spinner('Recalculating player projections and comparisons...'):
                try:
                    first=subprocess.run([sys.executable,str(ROOT/model),'--current-weight',str(current/100)],cwd=ROOT,capture_output=True,text=True,timeout=360)
                    if first.returncode:
                        st.error('Projection generator failed; comparison was not rerun.')
                        st.code((first.stdout+'\n'+first.stderr)[-3500:])
                    else:
                        second=subprocess.run([sys.executable,str(ROOT/comparator)],cwd=ROOT,capture_output=True,text=True,timeout=120)
                        if second.returncode or 'No matched NFL props' in second.stdout or 'Matched PrizePicks props: 0' in second.stdout:
                            st.warning('Projections updated, but comparisons were not successfully refreshed.')
                            st.code((second.stdout+'\n'+second.stderr)[-3500:])
                        else:
                            st.session_state[key]=current
                            st.cache_data.clear()
                            st.success('Model and comparisons updated.')
                            st.rerun()
                except subprocess.TimeoutExpired:st.error('Data source timed out; try again later.')
                except Exception as exc:st.error(f'Unable to run model: {exc}')
    st.divider()
    st.write('**Data files**')
    for label,f in files.items():st.caption(f'{label.title()}: {f} · {modified(f)}')
    if sport=='NFL':
        st.info('NFL projections are recent-form + prior-season statistical baselines. They do not adjust for injuries, matchup, weather, or usage changes.')
    else:
        st.info('NBA recalculation requires the updated nba_model.py supporting --current-weight.')
    st.stop()

if page=='Model History':
    st.subheader(f'{sport} prediction history')
    st.caption('Immutable pregame snapshots. Results are not considered verified until a separate settlement process records actual player statistics.')
    history=read_file('model_history.csv')
    if history is None or history.empty:
        st.info('No prediction history yet. The scheduled refresh will begin recording eligible pregame lines after the model-history changes are merged.')
        st.stop()
    required_history={'Sport','Player','Stat','Line','Projection','Direction','CapturedAtUTC','Result'}
    if not required_history.issubset(history.columns):
        st.warning('History file has an unexpected format. Check model_history.csv.')
        st.stop()
    history=history[history['Sport'].astype(str).str.upper().eq(sport)].copy()
    if history.empty:
        st.info(f'No {sport} predictions have been captured yet.')
        st.stop()
    history['CapturedAtUTC']=pd.to_datetime(history['CapturedAtUTC'],utc=True,errors='coerce')
    history['GameStartsAtUTC']=pd.to_datetime(history.get('GameStartsAtUTC'),utc=True,errors='coerce')
    history['Result']=history['Result'].fillna('PENDING').astype(str).str.upper()
    history['Actual']=pd.to_numeric(history.get('Actual'),errors='coerce')
    history['Projection']=pd.to_numeric(history['Projection'],errors='coerce')
    history['Line']=pd.to_numeric(history['Line'],errors='coerce')
    history=history.dropna(subset=['CapturedAtUTC','Projection','Line'])
    settled=history[history['Result'].isin(['WIN','LOSS','PUSH']) & history['Actual'].notna()].copy()
    wins=int((settled['Result']=='WIN').sum())
    losses=int((settled['Result']=='LOSS').sum())
    decided=wins+losses
    a,b,c,d=st.columns(4)
    a.metric('Predictions saved',f'{len(history):,}')
    b.metric('Awaiting results',f"{(history['Result']=='PENDING').sum():,}")
    c.metric('Verified decisions',f'{decided:,}')
    d.metric('Verified hit rate',f'{wins/decided:.1%}' if decided else '—')
    if not decided:
        st.info('Hit rate is unavailable until game results are independently settled. A projection gap is not a verified win.')
    else:
        st.caption('Hit rate excludes pushes and unresolved predictions; it does not establish profitability.')
        settled['Absolute error']=(settled['Actual']-settled['Projection']).abs()
        st.metric('Projection mean absolute error',f"{settled['Absolute error'].mean():.2f}")
        by_stat=settled[settled['Result'].isin(['WIN','LOSS'])].groupby('Stat')['Result'].agg(
            Picks='size',Wins=lambda x:(x=='WIN').sum()
        ).reset_index()
        by_stat['Hit rate']=by_stat['Wins']/by_stat['Picks']
        st.markdown('#### Results by prop type')
        st.dataframe(by_stat,hide_index=True,use_container_width=True)
    st.markdown('#### Prediction archive')
    c1,c2=st.columns(2)
    with c1:
        player_filter=st.text_input('Search history by player',key=f'history_search_{sport}')
    with c2:
        result_filter=st.selectbox('Result',['All','PENDING','WIN','LOSS','PUSH'],key=f'history_result_{sport}')
    filtered=history
    if player_filter:
        filtered=filtered[filtered['Player'].astype(str).str.contains(player_filter,case=False,regex=False,na=False)]
    if result_filter!='All':
        filtered=filtered[filtered['Result'].eq(result_filter)]
    filtered=filtered.sort_values('CapturedAtUTC',ascending=False)
    cols=[c for c in ['CapturedAtUTC','GameStartsAtUTC','Player','Team','Stat','Sportsbook','Line','Projection','Direction','Result','Actual','ModelVersion'] if c in filtered.columns]
    st.dataframe(filtered[cols],hide_index=True,use_container_width=True)
    st.download_button('Download prediction history',filtered.to_csv(index=False).encode('utf-8'),f'{sport.lower()}_model_history.csv','text/csv')
    st.stop()

if page=='Model Performance':
    st.subheader(f'{sport} verified model performance')
    st.caption('Only independently settled predictions count. Pending predictions and pushes are excluded from win rate.')
    records=read_file('model_history.csv')
    if records is None or not {'Sport','Result','Actual','Projection','Line','Stat','Direction'}.issubset(records.columns):
        st.info('Verified model history is unavailable. No performance claims can be calculated.')
        st.stop()
    records=records[records['Sport'].astype(str).str.upper().eq(sport)].copy()
    records['Actual']=pd.to_numeric(records['Actual'],errors='coerce')
    records['Projection']=pd.to_numeric(records['Projection'],errors='coerce')
    records['Line']=pd.to_numeric(records['Line'],errors='coerce')
    records['Result']=records['Result'].fillna('PENDING').astype(str).str.upper()
    settled=records[records['Result'].isin(['WIN','LOSS','PUSH']) & records['Actual'].notna()].copy()
    decided=settled[settled['Result'].isin(['WIN','LOSS'])].copy()
    total=len(decided)
    wins=int(decided['Result'].eq('WIN').sum())
    errors=settled.dropna(subset=['Actual','Projection']).copy()
    c1,c2,c3,c4=st.columns(4)
    c1.metric('Verified decisions',f'{total:,}')
    c2.metric('Wins',f'{wins:,}')
    c3.metric('Verified hit rate',f'{wins/total:.1%}' if total else '—')
    c4.metric('Projection error (MAE)',f"{(errors['Actual']-errors['Projection']).abs().mean():.1f}" if not errors.empty else '—')
    if total<30:
        st.warning(f'Only {total} verified decisions for {sport}. This is a small sample; apparent trends may not persist.')
    if total==0:
        st.info('No independently settled wins or losses yet.')
        st.stop()
    st.markdown('#### Accuracy by prop type')
    grouped=decided.groupby('Stat')['Result'].agg(Decisions='size',Wins=lambda x:int(x.eq('WIN').sum())).reset_index()
    grouped['Hit rate']=grouped['Wins']/grouped['Decisions']
    grouped=grouped.sort_values(['Decisions','Hit rate'],ascending=False)
    st.dataframe(grouped,hide_index=True,use_container_width=True,
        column_config={'Hit rate':st.column_config.NumberColumn('Verified hit rate',format='percent')})
    st.caption('Compare sample sizes before interpreting hit rates. Small groups are especially noisy.')
    st.markdown('#### Does a larger projection gap actually help?')
    eligible=decided.dropna(subset=['Projection','Line']).copy()
    eligible['Relative gap']=((eligible['Projection']-eligible['Line']).abs()/
        eligible['Line'].abs().clip(lower=5)).astype(float)
    eligible['Gap group']=pd.cut(eligible['Relative gap'],
        bins=[-0.001,0.05,0.10,0.20,float('inf')],
        labels=['0–5%','5–10%','10–20%','20%+'])
    buckets=eligible.groupby('Gap group',observed=True)['Result'].agg(
        Decisions='size',Wins=lambda x:int(x.eq('WIN').sum())).reset_index()
    if not buckets.empty:
        buckets['Hit rate']=buckets['Wins']/buckets['Decisions']
        st.caption('These are historical outcomes, not a rule for choosing future bets.')
        st.bar_chart(buckets.set_index('Gap group')['Hit rate'],color='#6415D8')
        st.dataframe(buckets,hide_index=True,use_container_width=True,
            column_config={'Hit rate':st.column_config.NumberColumn('Hit rate',format='percent')})
    st.caption('Descriptive historical analysis only. Thresholds are not optimized or validated on unseen games, and a higher hit rate does not necessarily imply profit.')
    if sport=='NBA':
        backtest=read_file('nba_backtest_summary.csv')
        if backtest is not None and {'Stat','RecentMAE','BlendedMAE'}.issubset(backtest.columns):
            with st.expander('Historical projection backtest'):
                st.dataframe(backtest,use_container_width=True,hide_index=True)
                st.caption('Backtest projection error is not the same as verified sportsbook hit rate.')
    st.stop()

if page=='Player Props':
    st.subheader(f'{sport} player projections')
    if projections is None or projections.empty:
        st.info(f'No {sport} projections yet. Run '+('nba_model.py' if sport=='NBA' else 'nfl_model.py')+' first.')
    else:
        data=projections.copy()
        search=st.text_input('Find a player',placeholder='Search by player name')
        if search:data=data[data['Player'].astype(str).str.contains(search,case=False,regex=False,na=False)]
        data.insert(0,'Headshot',data['Player'].map(lambda n:photo(n,sport)))
        if 'Player' in data.columns:
            if 'injury_lookup' not in locals():
                injury_lookup, _, _=injury_report(sport)
            data['Injury status']=data['Player'].map(lambda n:injury_lookup.get(norm(n),'UNVERIFIED'))
        cols=['Headshot']+[c for c in ['Player','Team','Stat','Projection','Points','Rebounds','Assists','Threes','Last5Avg','Last10Avg','Games','Injury status'] if c in data.columns]
        st.dataframe(data[cols],use_container_width=True,hide_index=True,column_config={'Headshot':st.column_config.ImageColumn('Photo',width='small')})
        st.caption(f'{len(data)} rows · {modified(files["projections"])}')
        available=sorted(data['Player'].dropna().astype(str).unique())
        if available:
            selected_player=st.selectbox('View player game logs',available,key=f'logs_player_{sport}')
            selected_rows=data[data['Player'].eq(selected_player)]
            pid=selected_rows['PlayerID'].iloc[0] if 'PlayerID' in selected_rows else None
            show_recent_games(sport,selected_player,player_id=pid)
    st.stop()

if comparison.empty and page!='Overview':
    st.warning(f'No {sport} comparisons yet. Generate projections, download sportsbook lines, and run the comparison script.')
    if sport=='NFL':
        st.code('python3 nfl_model.py\npython3 nfl_prizepicks_api.py\npython3 nfl_compare.py',language='bash')
    st.stop()

def render_player_gallery(rows, sport, limit=6):
    """Compact, PrizePicks-inspired tiles with optional details."""
    if rows is None or rows.empty:
        return
    shortlist=rows.head(limit)
    st.markdown('#### Quick prop cards')
    st.caption('Line = sportsbook target · Model = estimated stat · Lean is not a guaranteed outcome.')
    for index, (_, r) in enumerate(shortlist.iterrows()):
        with st.container(border=True):
            st.markdown('**'+str(r['Player'])+'** · '+str(r.get('Team',''))+' · '+str(r.get('Stat','')))
            line=pd.to_numeric(r.get('PrizePicksLine'),errors='coerce')
            model=pd.to_numeric(r.get('ModelProjection'),errors='coerce')
            gap=pd.to_numeric(r.get('Difference'),errors='coerce')
            line_label=f'{line:.1f}' if pd.notna(line) else '—'
            model_label=f'{model:.1f}' if pd.notna(model) else '—'
            gap_label=f'{gap:+.1f}' if pd.notna(gap) else '—'
            st.markdown(f'**Sportsbook:** {line_label}　 ·　 **Model:** {model_label}　 ·　 **Gap:** {gap_label}　 ·　 **Lean:** {r.get("Model lean","—")}')
            with st.expander('Last 5 games · chart & details'):
                st.caption('Injury: '+str(r.get('Injury status','UNVERIFIED')))
                if 'PickQuality' in r and pd.notna(r['PickQuality']):
                    st.caption('Screening: '+str(r['PickQuality'])+' (not a probability)')
                show_recent_games(sport,str(r['Player']),str(r['Stat']))

if page=='Overview':
    # User-supplied hero art can be placed in the repository as assets/propified_banner.jpg.
    # No synthetic player statistics or image-derived KPI values are used.
    banner=ROOT/'assets'/'propified_banner.jpg'
    if banner.exists():
        st.image(str(banner),use_container_width=True)
    else:
        st.markdown("""<div class="pf-home-hero"><div class="pf-hero-glow"></div>
        <div class="pf-home-logo"><span class="pf-bars">▂▅▇</span>│ Propified</div>
        <div class="pf-home-tag">PLAYER PROPS &nbsp; / &nbsp; PROJECTIONS &nbsp; / &nbsp; EDGES</div>
        </div>""",unsafe_allow_html=True)
    history=read_file('model_history.csv')
    wins=losses=settled_count=saved_count=0
    if history is not None and {'Sport','Result','Actual'}.issubset(history.columns):
        past=history[history['Sport'].astype(str).str.upper().eq(sport)].copy()
        saved_count=len(past)
        actual=pd.to_numeric(past['Actual'],errors='coerce')
        results=past['Result'].fillna('PENDING').astype(str).str.upper()
        verified=actual.notna() & results.isin(['WIN','LOSS','PUSH'])
        settled_count=int(verified.sum())
        wins=int((verified & results.eq('WIN')).sum())
        losses=int((verified & results.eq('LOSS')).sum())
    st.markdown('<div class="pf-section-space"></div>',unsafe_allow_html=True)
    k1,k2,k3,k4=st.columns(4)
    k1.metric(f'{sport} HIT RATE',f'{wins/(wins+losses):.1%}' if wins+losses else '—',help=f'{wins} verified wins / {wins+losses} decisions. Pushes and pending picks excluded.')
    k2.metric('SAVED PICKS',f'{saved_count:,}',help='Pregame model snapshots recorded for the selected sport.')
    k3.metric('AVAILABLE PROPS',f'{len(comparison):,}',help='Upcoming sportsbook props matched to model projections; not a measure of model accuracy.')
    k4.metric('SETTLED PICKS',f'{settled_count:,}',help='Verified wins, losses and pushes with recorded actual stats.')
    st.markdown('#### Explore today’s picks')
    nba_col,nfl_col=st.columns(2)
    with nba_col:
        st.markdown('<div class="pf-sport-label">🏀 NBA PROPS</div>',unsafe_allow_html=True)
        st.button('Today’s NBA Picks  →',key='home_nba',use_container_width=True,type='primary',on_click=navigate_to,args=('Betting Comparisons','NBA'))
        st.caption('Player projections, prop lines and model comparisons')
    with nfl_col:
        st.markdown('<div class="pf-sport-label">🏈 NFL PROPS</div>',unsafe_allow_html=True)
        st.button('Today’s NFL Picks  →',key='home_nfl',use_container_width=True,on_click=navigate_to,args=('Betting Comparisons','NFL'))
        st.caption('Player projections, prop lines and model comparisons')
    st.markdown('#### Today’s Top Props')
    if comparison.empty:
        st.info('No upcoming matched props are currently available. The verified history above remains accurate.')
    else:
        market_options=['All']+[x for x in ['Points','Rebounds','Assists','Threes','Passing Yards','Receiving Yards','Rushing Yards','Receptions'] if x in comparison['Stat'].astype(str).unique()]
        chosen_market=st.radio('Filter props',market_options,horizontal=True,key='home_market_'+sport)
        shown=comparison if chosen_market=='All' else comparison[comparison['Stat'].astype(str).eq(chosen_market)]
        shown=shown.sort_values(['ReliabilityScore','Gap'],ascending=False) if 'ReliabilityScore' in shown.columns else shown.sort_values('Gap',ascending=False)
        if shown.empty:
            st.info('No upcoming matched props in this category.')
        else:
            render_player_gallery(shown,sport,limit=6)
        st.caption(f'{len(shown)} upcoming matched props in this view · Model leans are not guaranteed winners.')
    st.stop()

else:st.subheader('Compare player props')
# Always keep the model results visible, even if no upcoming lines qualify.
st.markdown('### Model results & comparison table')
st.caption('Upcoming lines are shown first. Saved comparisons are historical snapshots and may no longer be available to bet.')
table_source=comparison if not comparison.empty else saved_comparison
if table_source is not None and not table_source.empty:
    available_cols=[c for c in ['Player','Team','Stat','PrizePicksLine','ModelProjection','Difference','GameStartsAt','ReliabilityScore','PickQuality'] if c in table_source.columns]
    st.dataframe(table_source[available_cols],hide_index=True,use_container_width=True)
    st.download_button('Download all model comparisons',table_source[available_cols].to_csv(index=False).encode('utf-8'),file_name=f'{sport.lower()}_model_results.csv',mime='text/csv',key='model_results_download')
elif projections is not None and not projections.empty:
    st.info('No matched sportsbook lines available. Showing model projections instead.')
    st.dataframe(projections,hide_index=True,use_container_width=True)
    st.download_button('Download projections',projections.to_csv(index=False).encode('utf-8'),file_name=f'{sport.lower()}_projections.csv',mime='text/csv',key='projection_results_download')
else:
    st.warning('No model projections or comparisons are currently available.')
if comparison.empty:
    st.info('No upcoming matched props right now. Historical comparisons above remain visible; refresh for new games.')
    st.stop()
board_mode=st.radio('Board view',['All comparisons','Top gaps'],horizontal=True,key=f'board_mode_{sport}')
st.caption('Top gaps highlights the largest model-to-line differences; it does not imply a higher chance of winning.')

f1,f2,f3,f4=st.columns([2,1.3,1.3,1.2])
with f1:search=st.text_input('Player search',placeholder='Search player')
with f2:teams=st.multiselect('Teams',sorted(comparison['Team'].dropna().astype(str).unique()))
with f3:stats=st.multiselect('Props',sorted(comparison['Stat'].dropna().astype(str).unique()))
with f4:direction=st.selectbox('Model lean',['All','OVER','UNDER','EVEN'])
minimum=st.slider('Minimum projection gap',0.0,float(max(5.0,comparison['Gap'].max())),0.0,0.5)
view=comparison.copy()
if search:view=view[view['Player'].astype(str).str.contains(search,case=False,regex=False,na=False)]
if teams:view=view[view['Team'].isin(teams)]
if stats:view=view[view['Stat'].isin(stats)]
if direction!='All':view=view[view['Model lean']==direction]
view=view[view['Gap']>=minimum]
if 'ReliabilityScore' in view.columns:
    view=view.sort_values(['ReliabilityScore','Gap'],ascending=False)
else:
    view=view.sort_values('Gap',ascending=False)
if board_mode=='Top gaps':view=view.sort_values('Gap',ascending=False).head(15)
st.caption(f'{len(view)} matching player props · gap = model projection minus sportsbook line')
if not view.empty:
    render_player_gallery(view,sport)
with st.expander('How to read this table'):
    st.markdown('**Sportsbook:** listed prop line. **Model:** statistical projection. **Gap:** difference between them. **Model lean:** which side the projection favors. **Injury status:** UNVERIFIED means the feed has not confirmed the player status.')

st.dataframe(view[['Headshot','Player','Team','Stat','PrizePicksLine','ModelProjection','Difference','Model lean','Injury status']+[c for c in ['PickQuality','ReliabilityScore'] if c in view.columns]],
    hide_index=True,use_container_width=True,column_config={
        'Headshot':st.column_config.ImageColumn('Photo',width='small'),
        'PrizePicksLine':st.column_config.NumberColumn('Sportsbook',format='%.1f'),
        'ModelProjection':st.column_config.NumberColumn('Model',format='%.1f'),
        'Difference':st.column_config.NumberColumn('Gap',format='%+.1f')})

if not view.empty:
    st.subheader('Player spotlight')
    options=view.reset_index(drop=True)
    choice=st.selectbox('Choose a player and prop',range(len(options)),format_func=lambda i:f"{options.iloc[i]['Player']} · {options.iloc[i]['Stat']}")
    player=options.iloc[choice]
    with st.container(border=True):
        pic,info=st.columns([1,5],vertical_alignment='center')
        with pic:
            if isinstance(player['Headshot'],str) and player['Headshot'].startswith('https://'):
                st.image(player['Headshot'],width=135)
            else:st.markdown('### ◉')
        with info:
            st.markdown(f"### {player['Player']}")
            st.caption(f"{player['Team']} · {player['Stat']} · {player['Model lean']} model lean · Injury: {player['Injury status']}")
            p1,p2,p3=st.columns(3)
            p1.metric('Sportsbook line',f"{player['PrizePicksLine']:.1f}")
            p2.metric('Model projection',f"{player['ModelProjection']:.1f}")
            p3.metric('Difference',f"{player['Difference']:+.1f}")
        chart=pd.DataFrame({'Value':[player['PrizePicksLine'],player['ModelProjection']]},index=['Sportsbook','Model'])
        st.bar_chart(chart,horizontal=True,color='#6415D8')
        if sport=='NFL':
            s1,s2=st.columns(2)
            for col,area in [('Last5Avg',s1),('Last10Avg',s2)]:
                if col in player and pd.notna(player[col]):area.metric(col.replace('Avg',' average'),f"{player[col]:.1f}")
        show_recent_games(sport,str(player['Player']),str(player['Stat']),player.get('PlayerID'))
        st.caption('Probability and value ratings require calibrated distributions and payout terms; no values are invented.')
    st.download_button('↓ Download comparisons',view.drop(columns=['Headshot']).to_csv(index=False).encode(),f'{sport.lower()}_comparisons.csv','text/csv')
st.divider()
st.caption('Propified · NBA data: nba_api · NFL data: nflverse / nflreadpy · Sportsbook lines: your ParlayAPI access. Validate player availability and game dates before making decisions.')