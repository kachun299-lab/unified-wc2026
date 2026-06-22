#!/usr/bin/env python3
"""
WC2026 Auto Data Updater - Smart Merge Version
Preserves manual match data, only updates standings/live scores from API
"""

import json
import requests
import os
import sys
from datetime import datetime, timezone, timedelta

API_KEY = os.environ.get('API_FOOTBALL_KEY', '')
API_BASE = 'https://v3.football.api-sports.io'
HEADERS = {
    'x-rapidapi-key': API_KEY,
    'x-rapidapi-host': 'v3.football.api-sports.io'
}
OUTPUT_FILE = 'data.json'


def log(msg):
    print(f"[WC2026] {msg}", flush=True)


def safe_get(obj, *keys, default=None):
    for key in keys:
        if not isinstance(obj, dict):
            return default
        obj = obj.get(key, default)
        if obj is None:
            return default
    return obj


def fetch_api(endpoint, params=None):
    if not API_KEY:
        log("WARNING: No API key found.")
        return None
    try:
        url = f"{API_BASE}{endpoint}"
        response = requests.get(url, headers=HEADERS, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        if data.get('errors'):
            log(f"API returned errors: {data['errors']}")
            return None
        return data.get('response', [])
    except Exception as e:
        log(f"API request failed: {e}")
        return None


def load_existing_data():
    try:
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        log("Creating new data template")
        return create_template()


def create_template():
    hk_tz = timezone(timedelta(hours=8))
    now = datetime.now(hk_tz)
    return {
        "last_updated": now.isoformat(),
        "meta": {
            "date_display": now.strftime("%Y年%m月%d日"),
            "round_info": "世界盃小組賽",
            "round": "R3",
            "version": "3.3.42",
            "source": "UNIFIED Framework"
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
    """Update match scores/status from API, but preserve manual match list if API returns different matches"""
    today = datetime.now().strftime("%Y-%m-%d")
    existing_matches = data.get('matches', {}).get('today', [])
    existing_live = data.get('matches', {}).get('live', [])

    if not existing_matches:
        log("No existing matches in data.json")
        return data

    # Find World Cup league ID
    leagues = fetch_api('/leagues', {'search': 'World Cup'})
    wc_league_id = None
    wc_season = 2026

    if leagues:
        for league in leagues:
            league_name = safe_get(league, 'league', 'name', default='')
            if 'World Cup' in league_name:
                wc_league_id = safe_get(league, 'league', 'id')
                log(f"Found World Cup league ID: {wc_league_id}")
                break

    if not wc_league_id:
        log("Could not find World Cup league ID, keeping existing match data")
        return data

    # Fetch fixtures for today
    fixtures = fetch_api('/fixtures', {
        'league': wc_league_id,
        'season': wc_season,
        'date': today,
        'timezone': 'Asia/Hong_Kong'
    })

    if not fixtures:
        log("No fixtures from API, keeping existing match data")
        return data

    # Build a map of existing matches by team names for quick lookup
    existing_map = {}
    for m in existing_matches:
        key = f"{m.get('home', '')} vs {m.get('away', '')}"
        existing_map[key.lower()] = m

    # Try to update existing matches with live scores from API
    api_matches_found = 0
    for fixture in fixtures:
        try:
            home_name = safe_get(fixture, 'teams', 'home', 'name', default='')
            away_name = safe_get(fixture, 'teams', 'away', 'name', default='')
            lookup_key = f"{home_name} vs {away_name}".lower()

            # Check if this API match matches any of our existing matches
            matched = False
            for key in existing_map:
                if home_name.lower() in key and away_name.lower() in key:
                    # Update score and status for this match
                    existing_match = existing_map[key]
                    status_short = safe_get(fixture, 'fixture', 'status', 'short', default='NS')

                    if status_short in ['1H', 'HT', '2H', 'ET', 'P']:
                        existing_match['status'] = 'live'
                    elif status_short in ['FT', 'AET', 'PEN']:
                        existing_match['status'] = 'finished'

                    home_goals = safe_get(fixture, 'goals', 'home')
                    away_goals = safe_get(fixture, 'goals', 'away')
                    if home_goals is not None and away_goals is not None:
                        existing_match['score'] = f"{home_goals} - {away_goals}"

                    existing_match['live_time'] = safe_get(fixture, 'fixture', 'status', 'elapsed')
                    api_matches_found += 1
                    matched = True
                    break

            if not matched:
                log(f"API match '{home_name} vs {away_name}' not found in existing data, skipping")

        except Exception as e:
            log(f"Error processing fixture: {e}")
            continue

    log(f"Updated {api_matches_found} existing matches with live data from API")

    # Update the data with modified existing matches
    data['matches']['today'] = existing_matches
    data['matches']['live'] = [m for m in existing_matches if m.get('status') == 'live']

    return data


def update_standings(data):
    leagues = fetch_api('/leagues', {'search': 'World Cup'})
    wc_league_id = None
    wc_season = 2026

    if leagues:
        for league in leagues:
            if 'World Cup' in safe_get(league, 'league', 'name', default=''):
                wc_league_id = safe_get(league, 'league', 'id')
                break

    if not wc_league_id:
        log("Could not find World Cup league ID for standings")
        return data

    standings = fetch_api('/standings', {
        'league': wc_league_id,
        'season': wc_season
    })

    if not standings:
        log("No standings data available")
        return data

    try:
        groups = {}
        league_data = safe_get(standings[0], 'league', default={})
        standings_list = safe_get(league_data, 'standings', default=[])

        for group_data in standings_list:
            if not group_data:
                continue
            for subgroup in group_data:
                if not subgroup or len(subgroup) == 0:
                    continue
                group_name = safe_get(subgroup[0], 'group', default='A')[-1] if subgroup else 'A'
                teams = []
                for team in subgroup:
                    try:
                        teams.append({
                            "team": safe_get(team, 'team', 'name', default='Unknown'),
                            "flag": safe_get(team, 'team', 'logo', default=''),
                            "played": safe_get(team, 'all', 'played', default=0),
                            "won": safe_get(team, 'all', 'win', default=0),
                            "drawn": safe_get(team, 'all', 'draw', default=0),
                            "lost": safe_get(team, 'all', 'lose', default=0),
                            "gf": safe_get(team, 'all', 'goals', 'for', default=0),
                            "ga": safe_get(team, 'all', 'goals', 'against', default=0),
                            "pts": safe_get(team, 'points', default=0)
                        })
                    except Exception:
                        continue
                if teams:
                    groups[group_name] = teams

        if groups:
            data['groups'] = groups
            log(f"Updated standings for {len(groups)} groups")
    except Exception as e:
        log(f"Error processing standings: {e}")

    return data


def update_timestamp(data):
    hk_tz = timezone(timedelta(hours=8))
    now = datetime.now(hk_tz)
    data['last_updated'] = now.isoformat()
    data['meta']['date_display'] = now.strftime("%Y年%m月%d日")
    return data


def save_data(data):
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        log(f"Data saved to {OUTPUT_FILE}")
        return True
    except Exception as e:
        log(f"Error saving data: {e}")
        return False


def main():
    log("=" * 50)
    log("WC2026 Auto Data Updater v3.3.42")
    log("=" * 50)

    if not API_KEY:
        log("WARNING: API_FOOTBALL_KEY not set! Using fallback data.")

    data = load_existing_data()
    existing_count = len(data.get('matches', {}).get('today', []))
    log(f"Loaded existing data with {existing_count} matches (last updated: {data.get('last_updated', 'N/A')})")

    log("Fetching today's matches from API...")
    data = update_matches(data)

    log("Fetching group standings from API...")
    data = update_standings(data)

    data = update_timestamp(data)

    if save_data(data):
        final_count = len(data.get('matches', {}).get('today', []))
        log(f"Update complete! {final_count} matches in data. Last updated: {data['last_updated']}")
    else:
        log("ERROR: Failed to save data!")
        sys.exit(1)

    log("=" * 50)


if __name__ == '__main__':
    main()
