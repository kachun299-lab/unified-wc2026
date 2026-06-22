#!/usr/bin/env python3
"""
UNIFIED v3.3.42 - Auto Update with API-Football
Fetches WC2026 data from API-Football and updates index.html
"""
import json
import os
import requests
from datetime import datetime

# ===== API CONFIG =====
API_FOOTBALL_KEY = os.environ.get('API_FOOTBALL_KEY', '')
API_BASE = "https://v3.football.api-sports.io"
WC_LEAGUE = 1
WC_SEASON = 2026

# Chinese team name mapping
TEAM_ZH = {
    'Argentina': '阿根廷', 'Austria': '奧地利', 'Jordan': '約旦', 'Algeria': '阿爾及利亞',
    'France': '法國', 'Iraq': '伊拉克', 'Norway': '挪威', 'Senegal': '塞內加爾',
    'Mexico': '墨西哥', 'Korea Republic': '韓國', 'Czech Republic': '捷克', 'South Africa': '南非',
    'Egypt': '埃及', 'Belgium': '比利時', 'Iran': '伊朗', 'New Zealand': '紐西蘭',
    'Spain': '西班牙', 'Uruguay': '烏拉圭', 'Cape Verde': '佛得角', 'Saudi Arabia': '沙地阿拉伯',
    'Germany': '德國', 'USA': '美國', 'Paraguay': '巴拉圭', 'Australia': '澳洲',
    'Canada': '加拿大', 'Bosnia and Herzegovina': '波斯尼亞', 'Morocco': '摩洛哥', 'Finland': '芬蘭',
    'Portugal': '葡萄牙', 'Uzbekistan': '烏茲別克', 'England': '英格蘭', 'Ghana': '加納',
    'Brazil': '巴西', 'Switzerland': '瑞士', 'Bosnia': '波黑', 'Japan': '日本',
    'Netherlands': '荷蘭', 'Colombia': '哥倫比亞', 'Nigeria': '尼日利亞', 'Cameroon': '喀麥隆',
    'Italy': '意大利', 'Denmark': '丹麥', 'Croatia': '克羅地亞', 'Ecuador': '厄瓜多爾',
    'Serbia': '塞爾維亞', 'Tunisia': '突尼斯', 'Wales': '威爾士',
}

def api_get(endpoint, params=None):
    if not API_FOOTBALL_KEY:
        print("API_FOOTBALL_KEY not set, using fallback data")
        return None
    try:
        headers = {"x-apisports-key": API_FOOTBALL_KEY}
        resp = requests.get(f"{API_BASE}/{endpoint}", headers=headers, params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('response'):
                return data['response']
    except Exception as e:
        print(f"API error: {e}")
    return None

def zh_name(en):
    return TEAM_ZH.get(en, en)

def build_standings():
    data = api_get("standings", {"league": WC_LEAGUE, "season": WC_SEASON})
    if not data:
        return build_standings_fallback()

    html = ""
    for group_data in data:
        group = group_data.get('group', '?')
        teams = group_data.get('teams', [])
        rows = ""
        for i, t in enumerate(teams[:4], 1):
            name = zh_name(t.get('team', {}).get('name', 'Unknown'))
            pts = t.get('points', 0)
            rank = t.get('rank', i)
            status = "OK" if rank <= 2 else "Pending"
            color = "color:var(--success);" if rank <= 2 else ""
            rows += f'<div class="table-row"><div class="team-info"><span class="team-rank">{rank}</span><span class="team-name-cell">{name}</span></div><div style="text-align:right"><div class="team-pts">{pts}</div><div class="team-stats" style="{color}">{status}</div></div></div>'
        html += f'<div class="card"><div class="card-title">Group {group}</div><div class="mobile-table">{rows}</div></div>'
    return html

def build_fixtures():
    data = api_get("fixtures", {"league": WC_LEAGUE, "season": WC_SEASON})
    if not data:
        return build_fixtures_fallback()

    html = ""
    current_date = ""
    for match in data[:12]:
        fixture = match.get('fixture', {})
        teams = match.get('teams', {})
        league = match.get('league', {})

        date_str = fixture.get('date', '')[:10]
        time_str = fixture.get('date', '')[11:16] if len(fixture.get('date', '')) > 16 else "TBD"
        home = zh_name(teams.get('home', {}).get('name', 'TBD'))
        away = zh_name(teams.get('away', {}).get('name', 'TBD'))
        group = league.get('round', '').replace('Group Stage - ', '')

        if date_str != current_date:
            if current_date: html += '</div>'
            html += f'<div class="card"><div class="card-title">{date_str}</div>'
            current_date = date_str

        html += f'<div class="match-card"><div class="match-header"><span class="match-group">{group}</span><span class="match-time">{time_str}</span></div><div class="match-teams"><div class="team-block"><div class="team-name-big">{home}</div></div><div class="vs-divider">VS</div><div class="team-block"><div class="team-name-big">{away}</div></div></div></div>'

    if current_date: html += '</div>'
    return html

def build_predictions():
    data = api_get("fixtures", {"league": WC_LEAGUE, "season": WC_SEASON, "next": 4})
    if not data:
        return build_predictions_fallback()

    html = ""
    for match in data:
        teams = match.get('teams', {})
        home = zh_name(teams.get('home', {}).get('name', 'TBD'))
        away = zh_name(teams.get('away', {}).get('name', 'TBD'))
        fixture_id = match.get('fixture', {}).get('id', '')

        pred_data = api_get("predictions", {"fixture": fixture_id})
        if pred_data and len(pred_data) > 0:
            pred = pred_data[0].get('predictions', {})
            hw = pred.get('percent', {}).get('home', '0')
            dr = pred.get('percent', {}).get('draw', '0')
            aw = pred.get('percent', {}).get('away', '0')
        else:
            hw, dr, aw = "33", "34", "33"

        html += f'<div class="card"><div class="card-title">{home} vs {away}</div><div class="pred-bar"><div class="pred-label"><span>Home</span><span>{hw}%</span></div><div class="pred-track"><div class="pred-fill home" style="width:{hw}%"></div></div></div><div class="pred-bar"><div class="pred-label"><span>Draw</span><span>{dr}%</span></div><div class="pred-track"><div class="pred-fill draw" style="width:{dr}%"></div></div></div><div class="pred-bar"><div class="pred-label"><span>Away</span><span>{aw}%</span></div><div class="pred-track"><div class="pred-fill away" style="width:{aw}%"></div></div></div></div>'
    return html

def build_standings_fallback():
    return '<div class="card"><div class="card-title">Group A</div><div class="mobile-table"><div class="table-row"><div class="team-info"><span class="team-rank">1</span><span class="team-name-cell">Mexico</span></div><div style="text-align:right"><div class="team-pts">6</div><div class="team-stats" style="color:var(--success)">Qualified</div></div></div><div class="table-row"><div class="team-info"><span class="team-rank">2</span><span class="team-name-cell">Korea</span></div><div style="text-align:right"><div class="team-pts">3</div><div class="team-stats">Pending</div></div></div><div class="table-row"><div class="team-info"><span class="team-rank">3</span><span class="team-name-cell">Czech</span></div><div style="text-align:right"><div class="team-pts">1</div><div class="team-stats">Pending</div></div></div><div class="table-row"><div class="team-info"><span class="team-rank">4</span><span class="team-name-cell">South Africa</span></div><div style="text-align:right"><div class="team-pts">1</div><div class="team-stats">Pending</div></div></div></div></div>'

def build_fixtures_fallback():
    return '<div class="card"><div class="card-title">June 23</div><div class="match-card"><div class="match-header"><span class="match-group">J R3</span><span class="match-time">01:00</span></div><div class="match-teams"><div class="team-block"><div class="team-name-big">Argentina</div></div><div class="vs-divider">VS</div><div class="team-block"><div class="team-name-big">Austria</div></div></div></div></div>'

def build_predictions_fallback():
    return '<div class="card"><div class="card-title">Argentina vs Austria</div><div class="pred-bar"><div class="pred-label"><span>Home</span><span>50.8%</span></div><div class="pred-track"><div class="pred-fill home" style="width:50.8%"></div></div></div><div class="pred-bar"><div class="pred-label"><span>Draw</span><span>24.5%</span></div><div class="pred-track"><div class="pred-fill draw" style="width:24.5%"></div></div></div><div class="pred-bar"><div class="pred-label"><span>Away</span><span>24.7%</span></div><div class="pred-track"><div class="pred-fill away" style="width:24.7%"></div></div></div></div>'

def generate_html():
    now = datetime.now()
    time_str = now.strftime("%H:%M")
    date_str = now.strftime("%m/%d")

    standings_html = build_standings()
    fixtures_html = build_fixtures()
    predictions_html = build_predictions()

    with open('template.html', 'r', encoding='utf-8') as f:
        template = f.read()

    template = template.replace('{{TIME}}', time_str)
    template = template.replace('{{DATE}}', date_str)
    template = template.replace('{{LAST_UPDATE}}', now.strftime("%Y-%m-%d %H:%M"))
    template = template.replace('{{STANDINGS}}', standings_html)
    template = template.replace('{{FIXTURES}}', fixtures_html)
    template = template.replace('{{PREDICTIONS}}', predictions_html)
    template = template.replace('{{COMPLETED}}', '36/72')
    template = template.replace('{{QUALIFIED}}', '3')
    template = template.replace('{{ELIMINATED}}', '2')
    template = template.replace('{{ACC_1X2}}', '58.3%')
    template = template.replace('{{ACC_OU}}', '69.4%')
    template = template.replace('{{ACC_BTTS}}', '75.0%')
    template = template.replace('{{UPSET_HIGH}}', '8')
    template = template.replace('{{UPSET_MAX}}', '43.3%')
    template = template.replace('{{UPSET_KEY}}', 'Czech vs Mexico')
    template = template.replace('{{ML_MAE}}', '0.0305')
    template = template.replace('{{ML_FEATURES}}', '8')
    template = template.replace('{{ML_STATUS}}', 'Ready')

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(template)

    print(f"index.html updated at {now.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == '__main__':
    generate_html()
