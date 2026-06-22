#!/usr/bin/env python3
"""
WC2026 Auto Data Updater
Fetches live data from API-Football and updates data.json
Run: python update_data.py
"""

import json
import requests
import os
from datetime import datetime, timezone, timedelta

# API Configuration
API_KEY = os.environ.get('API_FOOTBALL_KEY', '5268ae5daae7ba1b20e8e1f963f221ff')
API_BASE = 'https://v3.football.api-sports.io'
HEADERS = {
    'x-rapidapi-key': API_KEY,
    'x-rapidapi-host': 'v3.football.api-sports.io'
}

# World Cup 2026 League ID (API-Football)
WC_LEAGUE_ID = 1  # Update this with actual World Cup league ID
WC_SEASON = 2026

OUTPUT_FILE = 'data.json'


def fetch_api(endpoint, params=None):
    """Fetch data from API-Football"""
    try:
        url = f"{API_BASE}{endpoint}"
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        if data.get('errors'):
            print(f"API Error: {data['errors']}")
            return None
        return data.get('response', [])
    except Exception as e:
        print(f"Fetch error: {e}")
        return None


def load_existing_data():
    """Load existing data.json or create template"""
    try:
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return create_template()


def create_template():
    """Create initial data template"""
    return {
        "last_updated": datetime.now(timezone(timedelta(hours=8))).isoformat(),
        "meta": {
            "date_display": datetime.now().strftime("%Y年%m月%d日"),
            "round_info": "世界盃小組賽",
            "round": "R3",
            "version": "3.3.42"
        },
        "matches": {"today": [], "live": [], "upcoming": []},
        "groups": {},
        "predictions": {"selected": None, "matches": []},
        "motivation": {},
        "weather": {},
        "live_betting": {"alerts": [], "strategies": [], "time_segments": []},
        "analysis": {"corners": {}, "teams": [], "referee": {}}
    }


def update_matches(data):
    """Fetch and update today's matches from API"""
    today = datetime.now().strftime("%Y-%m-%d")

    # Fetch fixtures for today
    fixtures = fetch_api('/fixtures', {
        'league': WC_LEAGUE_ID,
        'season': WC_SEASON,
        'date': today,
        'timezone': 'Asia/Hong_Kong'
    })

    if not fixtures:
        print("No fixtures found or API error, keeping existing data")
        return data

    matches_today = []
    matches_live = []

    for fixture in fixtures:
        match_id = fixture['fixture']['id']
        status = fixture['fixture']['status']['short']

        match_data = {
            "id": match_id,
            "time": fixture['fixture']['date'].split('T')[1][:5] if 'T' in fixture['fixture']['date'] else "TBC",
            "home": fixture['teams']['home']['name'],
            "home_flag": fixture['teams']['home']['logo'],
            "home_fifa": f"FIFA #{fixture['teams']['home'].get('fifa_rank', 'N/A')}",
            "away": fixture['teams']['away']['name'],
            "away_flag": fixture['teams']['away']['logo'],
            "away_fifa": f"FIFA #{fixture['teams']['away'].get('fifa_rank', 'N/A')}",
            "group": fixture['league']['round'] or "",
            "status": "live" if status in ['1H', 'HT', '2H', 'ET', 'P'] else "upcoming" if status == 'NS' else "finished",
            "score": f"{fixture['goals']['home']} - {fixture['goals']['away']}" if fixture['goals']['home'] is not None else None,
            "live_time": fixture['fixture']['status']['elapsed'] if status in ['1H', 'HT', '2H'] else None,
            "predictions": {},
            "odds": {}
        }

        # Fetch predictions for this match
        predictions = fetch_api('/predictions', {'fixture': match_id})
        if predictions:
            pred = predictions[0]
            match_data['predictions'] = {
                "home": f"{pred['predictions']['winner']['id'] == pred['teams']['home']['id'] and pred['predictions']['winner']['comment'] or '50%'}",
                "draw": f"{pred['predictions']['draw'] or '25%'}",
                "away": f"{pred['predictions']['winner']['id'] == pred['teams']['away']['id'] and pred['predictions']['winner']['comment'] or '25%'}",
                "ou": f"大2.5 {pred['predictions']['over_under'] or '50%'}"
            }

        # Fetch odds
        odds = fetch_api('/odds', {'fixture': match_id, 'bookmaker': 1})
        if odds and odds[0].get('bookmakers'):
            bets = odds[0]['bookmakers'][0].get('bets', [])
            for bet in bets:
                if bet['name'] == 'Match Winner':
                    values = bet.get('values', [])
                    match_data['odds'] = {
                        "home": float(values[0]['odd']) if len(values) > 0 else 2.0,
                        "draw": float(values[1]['odd']) if len(values) > 1 else 3.2,
                        "away": float(values[2]['odd']) if len(values) > 2 else 3.5
                    }

        if match_data['status'] == 'live':
            matches_live.append(match_data)
        else:
            matches_today.append(match_data)

    data['matches']['today'] = matches_today
    data['matches']['live'] = matches_live

    return data


def update_standings(data):
    """Fetch and update group standings"""
    standings = fetch_api('/standings', {
        'league': WC_LEAGUE_ID,
        'season': WC_SEASON
    })

    if not standings:
        return data

    groups = {}
    for standing in standings[0].get('league', {}).get('standings', []):
        for group_data in standing:
            group_name = group_data[0]['group'][-1] if group_data else 'A'
            teams = []
            for team in group_data:
                teams.append({
                    "team": team['team']['name'],
                    "flag": team['team']['logo'],
                    "played": team['all']['played'],
                    "won": team['all']['win'],
                    "drawn": team['all']['draw'],
                    "lost": team['all']['lose'],
                    "gf": team['all']['goals']['for'],
                    "ga": team['all']['goals']['against'],
                    "pts": team['points']
                })
            groups[group_name] = teams

    if groups:
        data['groups'] = groups

    return data


def update_timestamp(data):
    """Update last updated timestamp"""
    hk_tz = timezone(timedelta(hours=8))
    data['last_updated'] = datetime.now(hk_tz).isoformat()
    data['meta']['date_display'] = datetime.now(hk_tz).strftime("%Y年%m月%d日")
    return data


def save_data(data):
    """Save data to JSON file"""
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Data saved to {OUTPUT_FILE}")


def main():
    print("=" * 50)
    print("WC2026 Auto Data Updater v3.3.42")
    print("=" * 50)

    # Load existing data
    data = load_existing_data()
    print(f"Loaded existing data (last updated: {data.get('last_updated', 'N/A')})")

    # Update matches
    print("\nFetching today's matches...")
    data = update_matches(data)

    # Update standings
    print("Fetching group standings...")
    data = update_standings(data)

    # Update timestamp
    data = update_timestamp(data)

    # Save
    save_data(data)
    print(f"\nUpdate complete! Last updated: {data['last_updated']}")
    print("=" * 50)


if __name__ == '__main__':
    main()
