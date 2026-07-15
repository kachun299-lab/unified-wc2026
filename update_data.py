import requests
import json
from datetime import datetime

class DataUpdater:
    def __init__(self, odds_api_key=None):
        self.odds_api_key = odds_api_key or "4cbc4c0d7cd3fb57b56bc8b43df411a6"  # ← 替換成你的 Key
        self.data = {
            "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "matches": []
        }

    def fetch_espn_scores(self, sport="basketball/nba"):
        """抓取即時比分"""
        try:
            url = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/scoreboard"
            resp = requests.get(url, timeout=10)
            events = resp.json().get("events", [])
            matches = []
            for event in events[:10]:
                comp = event["competitions"][0]
                home = comp["competitors"][0]
                away = comp["competitors"][1]
                matches.append({
                    "league": event.get("league", {}).get("name", sport.upper()),
                    "home": home["team"]["displayName"],
                    "away": away["team"]["displayName"],
                    "home_score": int(home.get("score", 0)),
                    "away_score": int(away.get("score", 0)),
                    "status": comp["status"]["type"]["shortDetail"]
                })
            return matches
        except:
            return []

    def fetch_bet365_odds(self):
        """抓取 Bet365 即時賠率（透過 The Odds API）"""
        try:
            url = "https://api.the-odds-api.com/v4/sports/soccer_world_cup/odds"
            params = {
                "apiKey": self.odds_api_key,
                "regions": "uk,eu",
                "markets": "h2h,totals",
                "oddsFormat": "decimal"
            }
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code != 200:
                return None

            events = resp.json()
            for event in events:
                for book in event.get("bookmakers", []):
                    if book["key"] == "bet365":
                        markets = {m["key"]: m["outcomes"] for m in book.get("markets", [])}
                        return {
                            "home_win": markets.get("h2h", [{}])[0].get("price"),
                            "draw": markets.get("h2h", [{}])[1].get("price"),
                            "away_win": markets.get("h2h", [{}])[2].get("price"),
                            "over": markets.get("totals", [{}])[0].get("price"),
                            "under": markets.get("totals", [{}])[1].get("price")
                        }
            return None
        except:
            return None

    def update_all(self):
        """完整更新所有聯賽 + Bet365 賠率"""
        # NBA Summer League
        self.data["matches"].extend(self.fetch_espn_scores("basketball/nba"))

        # WNBA
        self.data["matches"].extend(self.fetch_espn_scores("basketball/wnba"))

        # 世界盃足球 + Bet365 賠率
        football_matches = self.fetch_espn_scores("soccer/fifa.world")
        for match in football_matches:
            bet365 = self.fetch_bet365_odds()
            if bet365:
                match["bet365_odds"] = bet365
            self.data["matches"].append(match)

        # 儲存
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

        print(f"✅ 完整更新完成！共 {len(self.data['matches'])} 場比賽")
        print(f"更新時間: {self.data['last_update']}")
        return self.data


if __name__ == "__main__":
    updater = DataUpdater(odds_api_key="YOUR_THE_ODDS_API_KEY_HERE")  # ← 請替換
    updater.update_all()
