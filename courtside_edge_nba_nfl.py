"""COURTSIDE EDGE — combined NBA + NFL Streamlit dashboard.
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

st.set_page_config(page_title='Courtside Edge | NBA + NFL',page_icon='◉',layout='wide',initial_sidebar_state='expanded')
ROOT = Path(__file__).resolve().parent
C={'purple':'#6415D8','deep':'#4C0DB3','lavender':'#EDE3FF','background':'#FAFAFC','text':'#17142F','muted':'#696780','green':'#16A878','red':'#E34D64'}
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
:root{--ce-purple:#6415D8;--ce-deep:#4C0DB3;--ce-lavender:#EDE3FF;--ce-bg:#FAFAFC;--ce-panel:#FFFFFF;--ce-border:#E5E5EF;--ce-text:#17142F;--ce-muted:#696780}
html,body,[class*="css"],.stApp{font-family:'Inter',sans-serif;color:var(--ce-text)}
.stApp,[data-testid="stAppViewContainer"]{background:#FAFAFC!important;color:var(--ce-text)!important}
[data-testid="stHeader"]{background:rgba(250,250,252,.95)!important}
[data-testid="stSidebar"]{background:linear-gradient(165deg,#F6F1FF 0%,#FFFFFF 58%)!important;border-right:1px solid var(--ce-border)!important}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"]{gap:.7rem}
[data-testid="stSidebar"] .stRadio>div[role="radiogroup"]{gap:.3rem}
[data-testid="stSidebar"] .stRadio>div[role="radiogroup"] label{border-radius:11px;padding:9px 12px;transition:background .15s ease,color .15s ease}
[data-testid="stSidebar"] .stRadio>div[role="radiogroup"] label:hover{background:#F3ECFF}
[data-testid="stSidebar"] .stRadio>div[role="radiogroup"] label:has(input:checked){background:#EDE3FF;color:#4C0DB3!important;font-weight:700}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p{color:#696780}
.block-container{max-width:1400px!important;padding:2rem 2.5rem 5rem!important}
h1,h2,h3,h4{font-family:'Plus Jakarta Sans',sans-serif!important;color:#17142F!important;letter-spacing:-.035em!important}
h2{font-size:clamp(1.55rem,2.5vw,2.05rem)!important}
h3{font-size:1.2rem!important}
p,span,label{font-family:'Inter',sans-serif}
[data-testid="stMetric"]{background:#FFFFFF!important;border:1px solid #E5E5EF!important;border-radius:17px!important;padding:20px 22px!important;min-height:126px;box-shadow:0 3px 14px rgba(44,24,92,.025)!important}
[data-testid="stMetricLabel"]{color:#696780!important;font-size:.82rem!important}
[data-testid="stMetricValue"]{color:#17142F!important;font-family:'Plus Jakarta Sans',sans-serif!important;font-size:clamp(1.6rem,2.7vw,2.3rem)!important;letter-spacing:-.045em!important}
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
hr{border-color:#E5E5EF!important}
.hero{position:relative;overflow:hidden;background:#FFFFFF;border:1px solid #E5E5EF;border-radius:20px;padding:40px 44px;margin:8px 0 24px}
.hero:after{content:"";position:absolute;pointer-events:none;width:340px;height:340px;border-radius:50%;right:-125px;top:-195px;background:radial-gradient(circle,#EDE3FF 0%,#F6F1FF 60%,transparent 72%);opacity:.9}
.hero h1{position:relative;z-index:1;font-size:clamp(2.8rem,5.3vw,4.65rem)!important;line-height:1.07;margin:12px 0 13px;font-weight:800}
.hero p{position:relative;z-index:1;color:#696780;font-size:1rem;margin:0}
.eyebrow{position:relative;z-index:1;font-size:.73rem;color:#6415D8;letter-spacing:.16em;font-weight:800}
.smallprint{font-size:.78rem;color:#696780}
@media(max-width:900px){.block-container{padding:1.25rem 1.1rem 3rem!important}.hero{padding:28px 24px}.hero:after{width:220px;height:220px;right:-110px;top:-120px}}
@media(prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
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
def recent_game_logs(sport, player_name, player_id=None):
    if sport == 'NFL':
        import nflreadpy as nfl
        raw=nfl.load_player_stats([2025,2026],summary_level='week').to_pandas()
        name_col=next((c for c in ['player_name','player_display_name','player'] if c in raw),None)
        id_col=next((c for c in ['player_id','gsis_id'] if c in raw),None)
        if name_col is None:return pd.DataFrame()
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
    import requests
    from datetime import timedelta
    from concurrent.futures import ThreadPoolExecutor
    base='https://site.api.espn.com/apis/site/v2/sports/basketball/nba'
    session=requests.Session()
    def get(endpoint,params):
        response=session.get(base+endpoint,params=params,timeout=15)
        response.raise_for_status()
        return response.json()
    # ESPN athlete gamelog provides actual per-game statistics, not averages.
    pid=nba_player_ids().get(norm(player_name))
    if not pid:return pd.DataFrame()
    season=datetime.now().year if datetime.now().month>=10 else datetime.now().year
    # NBA season is named for its ending year.
    season=season+1 if datetime.now().month>=10 else season
    result=[]
    for year in [season,season-1]:
        try:
            data=get(f'/athletes/{pid}/gamelog',{'season':year})
        except (requests.RequestException,ValueError):
            continue
        labels=[]
        for group in data.get('labels',[]):
            if isinstance(group,list):labels.extend(group)
        if not labels:
            labels=data.get('labels',[])
        events=data.get('events',{})
        for entry in data.get('seasonTypes',[]):
            for category in entry.get('categories',[]):
                names=category.get('labels',labels)
                for item in category.get('events',[]):
                    event=events.get(str(item.get('eventId')), {})
                    if not event or not event.get('date'):continue
                    values=item.get('stats',[])
                    stats=dict(zip(names,values))
                    if not all(k in stats for k in ['PTS','REB','AST']):continue
                    try:
                        three=str(stats.get('3PT','0')).split('-')[0]
                        result.append({'Game':str(event['date'])[:10],
                          'Points':float(stats['PTS']),'Rebounds':float(stats['REB']),
                          'Assists':float(stats['AST']),'Threes':float(three)})
                    except (ValueError,TypeError):continue
        if len(result)>=5:break
    return pd.DataFrame(result).drop_duplicates('Game').sort_values('Game').tail(5)

def show_recent_games(sport, player_name, stat=None, player_id=None):
    st.markdown('#### Last 5 games')
    try:
        logs=recent_game_logs(sport,player_name,player_id)
    except Exception as exc:
        st.warning(f'Recent game logs are temporarily unavailable: {type(exc).__name__}.')
        return
    if logs.empty or len(logs.columns)<2:
        st.info('Verified per-game stats are not available for this player yet.')
        return
    choices=[c for c in logs.columns if c!='Game']
    default=choices.index(stat) if stat in choices else 0
    selected=st.selectbox('Stat to chart',choices,index=default,key=f'log_stat_{sport}_{norm(player_name)}')
    chart=logs[['Game',selected]].dropna().set_index('Game')
    if chart.empty:
        st.info('No completed games with this statistic.')
        return
    st.bar_chart(chart,color='#6415D8',use_container_width=True)
    st.caption(f'{len(chart)} recorded games · {selected} average: {chart[selected].mean():.1f} · Historical game logs, not model projections.')
    st.dataframe(logs,hide_index=True,use_container_width=True)

SPORT_FILES={'NBA':{'comparison':'nba_prizepicks_comparison.csv','projections':'todays_nba_projections.csv','lines':'prizepicks_nba_lines.csv'},
             'NFL':{'comparison':'nfl_comparison.csv','projections':'nfl_projections.csv','lines':'nfl_prizepicks_lines.csv'}}
with st.sidebar:
    st.markdown('### ◉ COURTSIDE **EDGE**')
    st.caption('THE PERFORMANCE LAB')
    st.divider()
    sport=st.radio('SPORT',['NBA','NFL'],horizontal=True)
    nav_icons={'Overview':'◫','Player Props':'♙','Betting Comparisons':'⇄','Top Gaps':'↗','Model History':'◷','Model Performance':'▥','Settings':'⚙'}
    page=st.radio('NAVIGATION',list(nav_icons),format_func=lambda name:f"{nav_icons[name]}   {name}",label_visibility='collapsed')
    st.divider()
    if st.button('↻ Refresh data',type='primary',use_container_width=True):
        st.cache_data.clear();st.rerun()
    st.caption('Hosted data · Courtside Edge repository')

files=SPORT_FILES[sport]
comparison=read_file(files['comparison'])
projections=read_file(files['projections'])
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
else:comparison=pd.DataFrame()

st.markdown(f'''<div class="hero"><span class="eyebrow">◉ COURTSIDE EDGE / {sport} ANALYTICS</span>
<h1>Find Your Edge<span style="color:#6415D8">.</span></h1>
<p>Player projections. Sportsbook lines. A clearer picture of the game.</p></div>''',unsafe_allow_html=True)
st.caption(f"{date.today():%A, %B %d, %Y}  ·  {sport} comparison updated: {modified(files['comparison'])}")
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


if page=='Settings':
    st.subheader(f'{sport} model controls')
    key=f'{sport.lower()}_weight'
    if key not in st.session_state:st.session_state[key]=60
    current=st.slider('Current season weight',0,100,st.session_state[key],5)
    a,b=st.columns(2)
    a.metric('Current season',f'{current}%')
    b.metric('Previous season',f'{100-current}%')
    st.caption('Weights always add to 100%. These apply to the projection generator, not to sportsbook lines.')
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

if comparison.empty:
    st.warning(f'No {sport} comparisons yet. Generate projections, download sportsbook lines, and run the comparison script.')
    if sport=='NFL':
        st.code('python3 nfl_model.py\npython3 nfl_prizepicks_api.py\npython3 nfl_compare.py',language='bash')
    st.stop()

def render_player_gallery(rows, sport, limit=6):
    """Compact, visual shortlist; scores are heuristic, never verified odds."""
    if rows is None or rows.empty:
        return
    shortlist=rows.drop_duplicates(subset=['Player']).head(limit)
    st.markdown('#### Players to explore')
    st.caption('Select a player below to view their sportsbook line, model projection and last-five-game performance. These are model leans, not verified picks.')
    columns=st.columns(3)
    for index,(_,r) in enumerate(shortlist.iterrows()):
        with columns[index % 3]:
            with st.container(border=True):
                pic,details=st.columns([1,2],vertical_alignment='center')
                with pic:
                    url=r.get('Headshot')
                    if isinstance(url,str) and url.startswith('https://'):
                        st.image(url,use_container_width=True)
                    else:
                        st.markdown('◉')
                with details:
                    st.markdown('**'+str(r['Player'])+'**')
                    st.caption(str(r.get('Team',''))+' · '+str(r.get('Stat','')))
                    st.markdown(f"**{r['Model lean']}** · {float(r['Difference']):+.1f} gap")
                with st.expander('View player details'):
                    x,y=st.columns(2)
                    x.metric('Sportsbook',f"{float(r['PrizePicksLine']):.1f}")
                    y.metric('Model',f"{float(r['ModelProjection']):.1f}")
                    if 'PickQuality' in r and pd.notna(r['PickQuality']):
                        st.caption('Screening: '+str(r['PickQuality'])+' (not a win probability)')
                    st.caption('Injury: '+str(r.get('Injury status','UNVERIFIED')))
                    if st.button('Load last 5 games',key=f"gallery_logs_{sport}_{index}_{norm(r['Player'])}_{norm(r['Stat'])}"):
                        st.session_state[f"gallery_open_{sport}_{index}_{norm(r['Player'])}"]=True
                    if st.session_state.get(f"gallery_open_{sport}_{index}_{norm(r['Player'])}",False):
                        show_recent_games(sport,str(r['Player']),str(r['Stat']))

if page=='Overview':
    st.subheader(f'{sport} comparison overview')
    a,b,c,d=st.columns(4)
    a.metric('Props analyzed',len(comparison))
    b.metric('OVER model leans',int((comparison['Difference']>0).sum()))
    c.metric('Largest projection gap',f"{comparison['Gap'].max():.1f}")
    recorded=read_file('model_history.csv')
    if recorded is not None and {'Sport','Result','Actual'}.issubset(recorded.columns):
        decided=recorded[recorded['Sport'].astype(str).str.upper().eq(sport)].copy()
        decided=decided[decided['Result'].astype(str).str.upper().isin(['WIN','LOSS']) & decided['Actual'].notna()]
        hit_rate=(decided['Result'].astype(str).str.upper()=='WIN').mean() if not decided.empty else None
        d.metric('Verified hit rate',f'{hit_rate:.1%}' if hit_rate is not None else '—')
    else:
        d.metric('Verified hit rate','—')
    st.caption('OVER and UNDER indicate projection direction, not guaranteed favorable bets.')
    st.markdown('#### What the numbers mean')
    with st.expander('Understand the model in 30 seconds'):
        st.markdown('**Sportsbook line:** the number posted by the sportsbook.  **Model projection:** the estimated player statistic.  **Gap:** projection minus line.  **OVER / UNDER:** the model\'s direction, not a guaranteed result.  **Verified hit rate:** settled wins divided by wins plus losses; pushes and pending picks are excluded.')
    render_player_gallery(comparison.sort_values(['ReliabilityScore','Gap'],ascending=False) if 'ReliabilityScore' in comparison.columns else comparison.sort_values('Gap',ascending=False),sport)

elif page=='Top Gaps':
    st.subheader('Largest projection gaps')
    st.caption('Candidates to review, not independently verified value picks.')
else:st.subheader('The comparison board')

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
if page=='Top Gaps':view=view.head(15)
st.caption(f'{len(view)} matching player props · gap = model projection minus sportsbook line')
if page in ('Top Gaps','Betting Comparisons') and not view.empty:
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
st.caption('Courtside Edge · NBA data: nba_api · NFL data: nflverse / nflreadpy · Sportsbook lines: your ParlayAPI access. Validate player availability and game dates before making decisions.')