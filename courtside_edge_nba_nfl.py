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
C={'navy':'#080F1D','panel':'#111D30','blue':'#2585FF','orange':'#FF9416','green':'#39FF88','red':'#FF4D5A','muted':'#91A4BB'}
st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap');
.stApp{background:radial-gradient(ellipse 85% 35% at 85% -15%,#15365d 0%,transparent 75%),#080F1D;color:#F4F8FF;font-family:'DM Sans',sans-serif}
[data-testid="stSidebar"]{background:#0D1829;border-right:1px solid #22344C}
.block-container{max-width:1480px;padding-top:1.7rem;padding-bottom:5rem}
h1,h2,h3{font-family:'Space Grotesk',sans-serif!important;letter-spacing:-.045em;color:#F4F8FF!important}
[data-testid="stMetric"]{background:linear-gradient(150deg,#17283F,#111D30);border:1px solid #293B53;border-radius:16px;padding:16px;min-height:112px}
[data-testid="stMetricLabel"]{color:#91A4BB}
[data-testid="stMetricValue"]{color:#F4F8FF;font-family:'Space Grotesk',sans-serif}
[data-testid="stVerticalBlockBorderWrapper"]>div{border:1px solid #263B55!important;background:#111D30!important;border-radius:16px!important}
.stButton button{border:1px solid #324860!important;border-radius:11px!important;background:#182A41!important;color:#F4F8FF!important;font-weight:700!important}
.stButton button:hover{border-color:#2585FF!important}
.stButton button[kind="primary"]{background:#2585FF!important;border-color:#2585FF!important}
[data-baseweb="input"]>div,[data-baseweb="select"]>div{background:#14243A!important;border-color:#2A3D55!important;color:#F4F8FF!important;border-radius:10px!important}
[data-baseweb="input"] input{color:#F4F8FF!important}
[data-testid="stDataFrame"]{border:1px solid #293B53;border-radius:13px;overflow:hidden}
[data-testid="stSlider"] [role="slider"]{background:#2585FF!important}
.hero{border-bottom:1px solid #24354B;padding:20px 0 24px;margin-bottom:20px}
.hero h1{font-size:clamp(2.8rem,5vw,4.6rem);line-height:1.05;margin:9px 0 7px}
.hero p{color:#91A4BB;font-size:1rem;margin:0}
.eyebrow{font-size:.7rem;color:#FF9416;letter-spacing:.2em;font-weight:800}
.smallprint{font-size:.78rem;color:#91A4BB}
</style>''',unsafe_allow_html=True)

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

SPORT_FILES={'NBA':{'comparison':'nba_prizepicks_comparison.csv','projections':'todays_nba_projections.csv','lines':'prizepicks_nba_lines.csv'},
             'NFL':{'comparison':'nfl_comparison.csv','projections':'nfl_projections.csv','lines':'nfl_prizepicks_lines.csv'}}
with st.sidebar:
    st.markdown('### ◉ COURTSIDE **EDGE**')
    st.caption('THE PERFORMANCE LAB')
    st.divider()
    sport=st.radio('SPORT',['NBA','NFL'],horizontal=True)
    page=st.radio('NAVIGATION',['Overview','Player Props','Betting Comparisons','Top Gaps','Model History','Model Performance','Settings'],label_visibility='collapsed')
    st.divider()
    if st.button('↻ Refresh data',use_container_width=True):
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
<h1>Find Your Edge<span style="color:#FF9416">.</span></h1>
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
    st.subheader(f'{sport} model performance')
    if sport=='NBA':
        history=read_file('nba_backtest_summary.csv')
        if history is not None and {'Stat','RecentMAE','BlendedMAE'}.issubset(history.columns):
            st.caption('Historical mean absolute error (MAE). Lower is better; this is not a betting win rate.')
            st.dataframe(history,use_container_width=True,hide_index=True)
            st.bar_chart(history.set_index('Stat')[['RecentMAE','BlendedMAE']])
            st.caption('Existing backtest does not validate the selected weighting or measure profitable bets.')
        else:st.info('No compatible NBA backtest summary found.')
    else:st.info('NFL backtesting has not been run yet. Historical accuracy and win rate are intentionally not shown.')
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
    st.stop()

if comparison.empty:
    st.warning(f'No {sport} comparisons yet. Generate projections, download sportsbook lines, and run the comparison script.')
    if sport=='NFL':
        st.code('python3 nfl_model.py\npython3 nfl_prizepicks_api.py\npython3 nfl_compare.py',language='bash')
    st.stop()

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
view=view[view['Gap']>=minimum].sort_values('Gap',ascending=False)
if page=='Top Gaps':view=view.head(15)
st.caption(f'{len(view)} matching player props')
st.dataframe(view[['Headshot','Player','Team','Stat','PrizePicksLine','ModelProjection','Difference','Model lean','Injury status']],
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
        st.bar_chart(chart,horizontal=True,color='#2585FF')
        if sport=='NFL':
            s1,s2=st.columns(2)
            for col,area in [('Last5Avg',s1),('Last10Avg',s2)]:
                if col in player and pd.notna(player[col]):area.metric(col.replace('Avg',' average'),f"{player[col]:.1f}")
        st.caption('Probability and value ratings require calibrated distributions and payout terms; no values are invented.')
    st.download_button('↓ Download comparisons',view.drop(columns=['Headshot']).to_csv(index=False).encode(),f'{sport.lower()}_comparisons.csv','text/csv')
st.divider()
st.caption('Courtside Edge · NBA data: nba_api · NFL data: nflverse / nflreadpy · Sportsbook lines: your ParlayAPI access. Validate player availability and game dates before making decisions.')