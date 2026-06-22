#!/usr/bin/env python3
"""
WC2026 Auto Data Updater - Fixed Version
Handles missing API keys and unexpected response structures
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
    """Safely navigate nested dicts"""
    for key in keys:
        if not isinstance(obj, dict):
            return default
        obj = obj.get(key, default)
        if obj is None:
            return default
    return obj


def fetch_api(endpoint, params=None):
    if not API_KEY:
        log("WARNING: No API key found. Using fallback data.")
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
    today = datetime.now().strftime("%Y-%m-%d")

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
        log("Could not find World Cup league ID, using fallback data")
        return data

    # Fetch fixtures
    fixtures = fetch_api('/fixtures', {
        'league': wc_league_id,
        'season': wc_season,
        'date': today,
        'timezone': 'Asia/Hong_Kong'
    })

    if not fixtures:
        log("No fixtures found for today, keeping existing data")
        return data

    matches_today = []
    matches_live = []

    for fixture in fixtures:
        try:
            match_id = safe_get(fixture, 'fixture', 'id')
            status_short = safe_get(fixture, 'fixture', 'status', 'short', default='NS')

            if status_short in ['1H', 'HT', '2H', 'ET', 'P']:
                status = 'live'
            elif status_short == 'NS':
                status = 'upcoming'
            elif status_short in ['FT', 'AET', 'PEN']:
                status = 'finished'
            else:
                status = 'upcoming'

            date_str = safe_get(fixture, 'fixture', 'date', default='')
            time_str = date_str.split('T')[1][:5] if 'T' in date_str else "TBC"

            home_goals = safe_get(fixture, 'goals', 'home')
            away_goals = safe_get(fixture, 'goals', 'away')
            score = f"{home_goals} - {away_goals}" if home_goals is not None else None

            match_data = {
                "id": match_id,
                "time": time_str,
                "home": safe_get(fixture, 'teams', 'home', 'name', default='Home'),
                "home_flag": safe_get(fixture, 'teams', 'home', 'logo', default=''),
                "home_fifa": f"FIFA #{safe_get(fixture, 'teams', 'home', 'fifa_rank', default='N/A')}",
                "away": safe_get(fixture, 'teams', 'away', 'name', default='Away'),
                "away_flag": safe_get(fixture, 'teams', 'away', 'logo', default=''),
                "away_fifa": f"FIFA #{safe_get(fixture, 'teams', 'away', 'fifa_rank', default='N/A')}",
                "group": safe_get(fixture, 'league', 'round', default=''),
                "status": status,
                "score": score,
                "live_time": safe_get(fixture, 'fixture', 'status', 'elapsed') if status == 'live' else None,
                "predictions": {},
                "odds": {}
            }

            # Fetch predictions
            predictions = fetch_api('/predictions', {'fixture': match_id})
            if predictions and len(predictions) > 0:
                pred = predictions[0]
                pred_data = safe_get(pred, 'predictions', default={})

                # Safely get prediction values with defaults
                draw_val = safe_get(pred_data, 'draw', default='25%')
                if draw_val is None:
                    draw_val = '25%'

                winner = safe_get(pred_data, 'winner', default={})
                winner_id = safe_get(winner, 'id')

                home_id = safe_get(pred, 'teams', 'home', 'id')
                away_id = safe_get(pred, 'teams', 'away', 'id')

                if winner_id and home_id and away_id:
                    home_prob = '68%' if winner_id == home_id else '35%'
                    away_prob = '68%' if winner_id == away_id else '35%'
                else:
                    home_prob = '50%'
                    away_prob = '25%'

                over_under = safe_get(pred_data, 'over_under', default='50%')
                if over_under is None:
                    over_under = '50%'

                match_data['predictions'] = {
                    "home": home_prob,
                    "draw": str(draw_val),
                    "away": away_prob,
                    "ou": f"大2.5 {over_under}"
                }
            else:
                match_data['predictions'] = {
                    "home": "50%", "draw": "25%", "away": "25%", "ou": "大2.5 50%"
                }

            # Fetch odds
            odds = fetch_api('/odds', {'fixture': match_id, 'bookmaker': 1})
            if odds and len(odds) > 0:
                bookmakers = safe_get(odds[0], 'bookmakers', default=[])
                if bookmakers and len(bookmakers) > 0:
                    bets = safe_get(bookmakers[0], 'bets', default=[])
                    for bet in bets:
                        if safe_get(bet, 'name') == 'Match Winner':
                            values = safe_get(bet, 'values', default=[])
                            if len(values) >= 3:
                                try:
                                    match_data['odds'] = {
                                        "home": float(values[0]['odd']),
                                        "draw": float(values[1]['odd']),
                                        "away": float(values[2]['odd'])
                                    }
                                except (KeyError, ValueError, IndexError):
                                    match_data['odds'] = {"home": 2.0, "draw": 3.2, "away": 3.5}
                            break

            if not match_data['odds']:
                match_data['odds'] = {"home": 2.0, "draw": 3.2, "away": 3.5}

            if status == 'live':
                matches_live.append(match_data)
            else:
                matches_today.append(match_data)

        except Exception as e:
            log(f"Error processing fixture: {e}")
            continue

    if matches_today or matches_live:
        data['matches']['today'] = matches_today
        data['matches']['live'] = matches_live
        log(f"Updated {len(matches_today)} upcoming + {len(matches_live)} live matches")
    else:
        log("No matches to update")

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
    log(f"Loaded existing data (last updated: {data.get('last_updated', 'N/A')})")

    log("Fetching today's matches...")
    data = update_matches(data)

    log("Fetching group standings...")
    data = update_standings(data)

    data = update_timestamp(data)

    if save_data(data):
        log(f"Update complete! Last updated: {data['last_updated']}")
    else:
        log("ERROR: Failed to save data!")
        sys.exit(1)

    log("=" * 50)


if __name__ == '__main__':
    main()
