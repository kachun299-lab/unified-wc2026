#!/usr/bin/env python3
"""
UNIFIED v3.3.43 - Enhanced Auto Update
Features: Live scores, multi-league, top scorers, half-time stats
"""
import json
from datetime import datetime

def load_data():
    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading data.json: {e}")
        return None

def build_standings(data):
    html = ""
    wc = data.get('leagues', {}).get('world_cup', {})
    for group, teams in wc.get('standings', {}).items():
        rows = ""
        for t in teams:
            status_color = f"color:var(--{t['status_color']});" if t['status_color'] != 'muted' else ""
            rows += f'<div class="table-row"><div class="team-info"><span class="team-rank">{t["rank"]}</span><span class="team-name-cell">{t["team"]}</span></div><div style="text-align:right"><div class="team-pts">{t["pts"]}</div><div class="team-stats" style="{status_color}">{t["status"]}</div></div></div>'
        html += f'<div class="card"><div class="card-title">&#127942; {group}組</div><div class="mobile-table">{rows}</div></div>'
    return html

def build_leagues(data):
    html = ""
    for league_key, league_data in data.get('leagues', {}).items():
        if league_key == 'world_cup':
            continue
        rows = ""
        for t in league_data.get('standings', []):
            gd_str = f"(+{t['gd']})" if t['gd'] > 0 else f"({t['gd']})"
            rows += f'<div class="table-row"><div class="team-info"><span class="team-rank">{t["rank"]}</span><span class="team-name-cell">{t["team"]}</span></div><div style="text-align:right"><div class="team-pts">{t["pts"]}分</div><div class="team-stats">{t["played"]}場 {gd_str}</div></div></div>'
        html += f'<div class="card"><div class="card-title">&#127942; {league_data["name"]}</div><div class="mobile-table">{rows}</div></div>'
    return html

def build_fixtures(data):
    html = ""
    current_date = ""
    for f in data.get('fixtures', []):
        if f['date'] != current_date:
            if current_date:
                html += '</div>'
            html += f'<div class="card"><div class="card-title">&#128197; {f["date"]}</div>'
            current_date = f['date']

        extra = f'<div style="font-size:0.75rem;color:var(--text-muted)">戰意: {f["home_mot"]} vs {f["away_mot"]} | 預期: {f["exp_goals"]}球</div>' if 'exp_goals' in f else ''
        html += f'<div class="match-card"><div class="match-header"><span class="match-group">{f["group"]}</span><span class="match-time">{f["time"]}</span></div><div class="match-teams"><div class="team-block"><div class="team-name-big">{f["home"]}</div></div><div class="vs-divider">VS</div><div class="team-block"><div class="team-name-big">{f["away"]}</div></div></div>{extra}</div>'

    if current_date:
        html += '</div>'
    return html

def build_predictions(data):
    html = ""
    for p in data.get('predictions', []):
        alert_desc = f'<span style="font-size:0.75rem;color:var(--text-muted);margin-left:0.5rem">{p["alert_desc"]}</span>' if p.get('alert_desc') else ''

        extra_stats = ""
        if p.get('exp_goals'):
            extra_stats += f'<div class="stat-row"><span class="stat-label">預期入球</span><span class="stat-value">{p["exp_goals"]}</span></div>'
        if p.get('over_3'):
            extra_stats += f'<div class="stat-row"><span class="stat-label">大3.0</span><span class="stat-value">{p["over_3"]}%</span></div>'
        if p.get('btts'):
            extra_stats += f'<div class="stat-row"><span class="stat-label">BTTS</span><span class="stat-value">{p["btts"]}%</span></div>'
        if p.get('corners'):
            extra_stats += f'<div class="stat-row"><span class="stat-label">角球</span><span class="stat-value">{p["corners"]}</span></div>'

        html += f'<div class="card"><div class="card-title">&#127919; {p["title"]}</div><div style="margin-bottom:0.75rem"><span class="alert-badge {p["alert_class"]}">{p["alert"]}</span>{alert_desc}</div><div class="pred-bar"><div class="pred-label"><span>主勝</span><span>{p["home_win"]}%</span></div><div class="pred-track"><div class="pred-fill home" style="width:{p["home_win"]}%"></div></div></div><div class="pred-bar"><div class="pred-label"><span>和局</span><span>{p["draw"]}%</span></div><div class="pred-track"><div class="pred-fill draw" style="width:{p["draw"]}%"></div></div></div><div class="pred-bar"><div class="pred-label"><span>客勝</span><span>{p["away_win"]}%</span></div><div class="pred-track"><div class="pred-fill away" style="width:{p["away_win"]}%"></div></div></div><div style="margin-top:0.75rem;font-size:0.8rem">{extra_stats}</div></div>'
    return html

def build_motivation(data):
    mot_high = ""
    for m in data.get('motivation_high', []):
        mot_high += f'<div class="mot-meter"><span class="mot-label">{m["team"]}</span><div class="mot-track"><div class="mot-fill high" style="width:{m["value"]*10}%"></div></div><span class="mot-value" style="color:var(--danger)">{m["value"]}</span></div><div style="font-size:0.7rem;color:var(--text-muted);margin-left:75px;margin-bottom:0.5rem">{m["desc"]}</div>'

    mot_low = ""
    for m in data.get('motivation_low', []):
        mot_low += f'<div class="mot-meter"><span class="mot-label">{m["team"]}</span><div class="mot-track"><div class="mot-fill low" style="width:{m["value"]*10}%"></div></div><span class="mot-value" style="color:var(--success)">{m["value"]}</span></div><div style="font-size:0.7rem;color:var(--text-muted);margin-left:75px;margin-bottom:0.5rem">{m["desc"]}</div>'

    return mot_high, mot_low

def build_live_scores(data):
    html = ""
    for match in data.get('live_scores', []):
        status_class = "live-indicator" if match['status'] == 'live' else ""
        status_text = f'<span class="live-indicator"><span class="live-dot"></span>LIVE {match["time"]}</span>' if match['status'] == 'live' else f'<span style="color:var(--text-muted)">完賽 {match["time"]}</span>'

        score_big = f'<div style="font-size:2rem;font-weight:800;text-align:center;margin:0.5rem 0"><span style="color:var(--primary)">{match["home_score"]}</span> <span style="color:var(--text-muted);font-size:1rem">-</span> <span style="color:var(--primary)">{match["away_score"]}</span></div>'

        ht_info = f'<div style="font-size:0.75rem;color:var(--text-muted);text-align:center">半場 {match["home_ht"]}:{match["away_ht"]}</div>' if match.get('home_ht') is not None else ''

        extra = ""
        if match.get('corners'):
            extra += f'<div class="stat-row"><span class="stat-label">角球</span><span class="stat-value">{match["corners"]}</span></div>'
        if match.get('next_goal_home'):
            extra += f'<div class="stat-row"><span class="stat-label">{match["home"]} 入球機率</span><span class="stat-value">{match["next_goal_home"]}%</span></div>'
        if match.get('next_goal_away'):
            extra += f'<div class="stat-row"><span class="stat-label">{match["away"]} 入球機率</span><span class="stat-value">{match["next_goal_away"]}%</span></div>'
        if match.get('corner_tip'):
            extra += f'<div class="stat-row"><span class="stat-label">角球建議</span><span class="stat-value up">{match["corner_tip"]}</span></div>'

        html += f'<div class="card"><div class="match-header"><span class="match-group">{match["league"]}</span>{status_text}</div><div class="match-teams"><div class="team-block"><div class="team-name-big">{match["home"]}</div></div><div class="vs-divider">VS</div><div class="team-block"><div class="team-name-big">{match["away"]}</div></div></div>{score_big}{ht_info}<div style="margin-top:0.5rem;font-size:0.8rem">{extra}</div></div>'

    return html

def build_top_scorers(data):
    html = ""
    for p in data.get('top_scorers', []):
        html += f'<div class="table-row"><div class="team-info"><span class="team-rank">{p["rank"]}</span><span class="team-name-cell">{p["player"]} ({p["team"]})</span></div><div style="text-align:right"><div class="team-pts">{p["goals"]}球</div><div class="team-stats">{p["assists"]}助攻</div></div></div>'

    return f'<div class="card"><div class="card-title">&#9917; 射手榜</div><div class="mobile-table">{html}</div></div>'

def generate_html():
    data = load_data()
    if not data:
        print("Failed to load data.json")
        return

    now = datetime.now()
    time_str = now.strftime("%H:%M")
    date_str = now.strftime("%-m月%-d日")

    standings_html = build_standings(data)
    leagues_html = build_leagues(data)
    fixtures_html = build_fixtures(data)
    predictions_html = build_predictions(data)
    mot_high, mot_low = build_motivation(data)
    live_scores_html = build_live_scores(data)
    top_scorers_html = build_top_scorers(data)

    stats = data.get('stats', {})

    with open('template.html', 'r', encoding='utf-8') as f:
        template = f.read()

    template = template.replace('{{TIME}}', time_str)
    template = template.replace('{{DATE}}', date_str)
    template = template.replace('{{LAST_UPDATE}}', now.strftime("%Y-%m-%d %H:%M"))
    template = template.replace('{{STANDINGS}}', standings_html)
    template = template.replace('{{LEAGUES}}', leagues_html)
    template = template.replace('{{FIXTURES}}', fixtures_html)
    template = template.replace('{{PREDICTIONS}}', predictions_html)
    template = template.replace('{{MOT_HIGH}}', mot_high)
    template = template.replace('{{MOT_LOW}}', mot_low)
    template = template.replace('{{LIVE_SCORES}}', live_scores_html)
    template = template.replace('{{TOP_SCORERS}}', top_scorers_html)

    template = template.replace('{{COMPLETED}}', stats.get('completed', '36/72'))
    template = template.replace('{{QUALIFIED}}', stats.get('qualified', '3'))
    template = template.replace('{{ELIMINATED}}', stats.get('eliminated', '2'))
    template = template.replace('{{ACC_1X2}}', stats.get('accuracy_1x2', '58.3%'))
    template = template.replace('{{ACC_OU}}', stats.get('accuracy_ou', '69.4%'))
    template = template.replace('{{ACC_BTTS}}', stats.get('accuracy_btts', '75.0%'))
    template = template.replace('{{UPSET_HIGH}}', stats.get('upset_high', '8'))
    template = template.replace('{{UPSET_MAX}}', stats.get('upset_max', '43.3%'))
    template = template.replace('{{UPSET_KEY}}', stats.get('upset_key', '捷克vs墨西哥'))
    template = template.replace('{{ML_MAE}}', stats.get('ml_mae', '0.0305'))
    template = template.replace('{{ML_FEATURES}}', stats.get('ml_features', '8'))
    template = template.replace('{{ML_STATUS}}', stats.get('ml_status', '✅就緒'))

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(template)

    print(f"index.html updated at {now.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == '__main__':
    generate_html()
