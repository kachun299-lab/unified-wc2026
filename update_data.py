#!/usr/bin/env python3
"""
UNIFIED v3.3.43 - Auto Update with Correct Score Analysis
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
    for group, teams in data.get('standings', {}).items():
        rows = ""
        for t in teams:
            status_color = f"color:var(--{t['status_color']});" if t['status_color'] != 'muted' else ""
            rows += '<div class="table-row"><div class="team-info"><span class="team-rank">' + str(t["rank"]) + '</span><span class="team-name-cell">' + t["team"] + '</span></div><div style="text-align:right"><div class="team-pts">' + str(t["pts"]) + '</div><div class="team-stats" style="' + status_color + '">' + t["status"] + '</div></div></div>'
        html += '<div class="card"><div class="card-title">&#127942; ' + group + '組</div><div class="mobile-table">' + rows + '</div></div>'
    return html

def build_fixtures(data):
    html = ""
    current_date = ""
    for f in data.get('fixtures', []):
        if f['date'] != current_date:
            if current_date:
                html += '</div>'
            html += '<div class="card"><div class="card-title">&#128197; ' + f["date"] + '</div>'
            current_date = f['date']

        extra = '<div style="font-size:0.75rem;color:var(--text-muted)">戰意: ' + str(f.get("home_mot","")) + ' vs ' + str(f.get("away_mot","")) + ' | 預期: ' + str(f.get("exp_goals","")) + '球</div>' if 'exp_goals' in f else ''
        html += '<div class="match-card"><div class="match-header"><span class="match-group">' + f["group"] + '</span><span class="match-time">' + f["time"] + '</span></div><div class="match-teams"><div class="team-block"><div class="team-name-big">' + f["home"] + '</div></div><div class="vs-divider">VS</div><div class="team-block"><div class="team-name-big">' + f["away"] + '</div></div></div>' + extra + '</div>'

    if current_date:
        html += '</div>'
    return html

def build_predictions(data):
    html = ""
    for p in data.get('predictions', []):
        alert_desc = '<span style="font-size:0.75rem;color:var(--text-muted);margin-left:0.5rem">' + p.get("alert_desc","") + '</span>' if p.get('alert_desc') else ''

        extra_stats = ""
        if p.get('exp_goals'):
            extra_stats += '<div class="stat-row"><span class="stat-label">預期入球</span><span class="stat-value">' + str(p["exp_goals"]) + '</span></div>'
        if p.get('over_3'):
            extra_stats += '<div class="stat-row"><span class="stat-label">大3.0</span><span class="stat-value">' + str(p["over_3"]) + '%</span></div>'
        if p.get('btts'):
            extra_stats += '<div class="stat-row"><span class="stat-label">BTTS</span><span class="stat-value">' + str(p["btts"]) + '%</span></div>'
        if p.get('corners'):
            extra_stats += '<div class="stat-row"><span class="stat-label">角球</span><span class="stat-value">' + str(p["corners"]) + '</span></div>'

        html += '<div class="card"><div class="card-title">&#127919; ' + p["title"] + '</div><div style="margin-bottom:0.75rem"><span class="alert-badge ' + p["alert_class"] + '">' + p["alert"] + '</span>' + alert_desc + '</div><div class="pred-bar"><div class="pred-label"><span>主勝</span><span>' + str(p["home_win"]) + '%</span></div><div class="pred-track"><div class="pred-fill home" style="width:' + str(p["home_win"]) + '%"></div></div></div><div class="pred-bar"><div class="pred-label"><span>和局</span><span>' + str(p["draw"]) + '%</span></div><div class="pred-track"><div class="pred-fill draw" style="width:' + str(p["draw"]) + '%"></div></div></div><div class="pred-bar"><div class="pred-label"><span>客勝</span><span>' + str(p["away_win"]) + '%</span></div><div class="pred-track"><div class="pred-fill away" style="width:' + str(p["away_win"]) + '%"></div></div></div><div style="margin-top:0.75rem;font-size:0.8rem">' + extra_stats + '</div></div>'
    return html

def build_correct_scores(data):
    html = ""
    for cs in data.get('correct_scores', []):
        top = cs['top_pick']
        top_prob = cs['top_prob']
        top_odds = next((x["odds"] for x in cs["scores"] if x["score"]==top), "-")

        score_rows = ""
        for i, s in enumerate(cs['scores'][:5]):
            is_top = s['score'] == top
            highlight = 'style="background:rgba(0,212,170,0.15);border:1px solid var(--primary);"' if is_top else ''
            top_badge = '<span style="font-size:0.6rem;color:var(--primary);margin-left:0.3rem">&#9733; 首選</span>' if is_top else ''
            score_rows += '<div class="cs-row" ' + highlight + '><span class="cs-score">' + s["score"] + '</span><span class="cs-prob">' + str(s["prob"]) + '%</span><span class="cs-odds">' + str(s["odds"]) + '</span>' + top_badge + '</div>'

        top_section = '<div class="cs-top-pick"><div style="font-size:0.8rem;color:var(--text-muted);margin-bottom:0.3rem">最高概率波膽</div><div style="font-size:2rem;font-weight:800;color:var(--primary);text-align:center">' + top + '</div><div style="font-size:0.9rem;color:var(--accent);text-align:center">' + str(top_prob) + '% | 賠率 ' + str(top_odds) + '</div></div>'

        html += '<div class="card"><div class="card-title">&#127922; ' + cs["match"] + '</div>' + top_section + '<div style="margin-top:0.75rem"><div style="font-size:0.8rem;color:var(--text-muted);margin-bottom:0.5rem">波膽概率排行</div>' + score_rows + '</div></div>'
    return html

def build_motivation(data):
    mot_high = ""
    for m in data.get('motivation_high', []):
        mot_high += '<div class="mot-meter"><span class="mot-label">' + m["team"] + '</span><div class="mot-track"><div class="mot-fill high" style="width:' + str(m["value"]*10) + '%"></div></div><span class="mot-value" style="color:var(--danger)">' + str(m["value"]) + '</span></div><div style="font-size:0.7rem;color:var(--text-muted);margin-left:75px;margin-bottom:0.5rem">' + m["desc"] + '</div>'

    mot_low = ""
    for m in data.get('motivation_low', []):
        mot_low += '<div class="mot-meter"><span class="mot-label">' + m["team"] + '</span><div class="mot-track"><div class="mot-fill low" style="width:' + str(m["value"]*10) + '%"></div></div><span class="mot-value" style="color:var(--success)">' + str(m["value"]) + '</span></div><div style="font-size:0.7rem;color:var(--text-muted);margin-left:75px;margin-bottom:0.5rem">' + m["desc"] + '</div>'

    return mot_high, mot_low

def generate_html():
    data = load_data()
    if not data:
        print("Failed to load data.json")
        return

    now = datetime.now()
    time_str = now.strftime("%H:%M")
    date_str = now.strftime("%-m月%-d日")

    standings_html = build_standings(data)
    fixtures_html = build_fixtures(data)
    predictions_html = build_predictions(data)
    correct_scores_html = build_correct_scores(data)
    mot_high, mot_low = build_motivation(data)

    stats = data.get('stats', {})

    with open('template.html', 'r', encoding='utf-8') as f:
        template = f.read()

    template = template.replace('{{TIME}}', time_str)
    template = template.replace('{{DATE}}', date_str)
    template = template.replace('{{LAST_UPDATE}}', now.strftime("%Y-%m-%d %H:%M"))
    template = template.replace('{{STANDINGS}}', standings_html)
    template = template.replace('{{FIXTURES}}', fixtures_html)
    template = template.replace('{{PREDICTIONS}}', predictions_html)
    template = template.replace('{{CORRECT_SCORES}}', correct_scores_html)
    template = template.replace('{{MOT_HIGH}}', mot_high)
    template = template.replace('{{MOT_LOW}}', mot_low)

    template = template.replace('{{COMPLETED}}', stats.get('completed', '36/72'))
    template = template.replace('{{QUALIFIED}}', stats.get('qualified', '3'))
    template = template.replace('{{ELIMINATED}}', stats.get('eliminated', '2'))
    template = template.replace('{{ACC_1X2}}', stats.get('accuracy_1x2', '58.3%'))
    template = template.replace('{{ACC_OU}}', stats.get('accuracy_ou', '69.4%'))
    template = template.replace('{{ACC_BTTS}}', stats.get('accuracy_btts', '75.0%'))
    template = template.replace('{{ACC_CS}}', stats.get('accuracy_cs', '32.1%'))
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
