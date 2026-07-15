import requests
import json
from datetime import datetime

class DataUpdater:
    def __init__(self, odds_api_key=None):
        self.odds_api_key = odds_api_key or "YOUR_THE_ODDS_API_KEY_HERE"  # ← 請替換成你的 Key
        self.data = {
            "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "matches": []
        }

    def calculate_xg(self, team_name):
        """簡單 xG 計算"""
        xg_map = {
            "英格蘭": 1.65,
            "阿根廷": 1.85,
            "明尼蘇達": 1.95,
            "洛杉磯": 1.45,
        }
        return xg_map.get(team_name, 1.55)

    def fetch_espn_scores(self, sport="basketball/nba"):
        """抓取即時比分"""
        try:
            url = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/scoreboard"
            resp = requests.get(url, timeout=10)
            events = resp.json().get("events", [])
            matches = []
            for event in events[:12]:
                comp = event["competitions"][0]
                home = comp["competitors"][0]
                away = comp["competitors"][1]
                
                matches.append({
                    "league": event.get("league", {}).get("name", sport.upper()),
                    "home": home["team"]["displayName"],
                    "away": away["team"]["displayName"],
                    "home_score": int(home.get("score", 0)),
                    "away_score": int(away.get("score", 0)),
                    "status": comp["status"]["type"]["shortDetail"],
                    "xg": {
                        "home_xg": self.calculate_xg(home["team"]["displayName"]),
                        "away_xg": self.calculate_xg(away["team"]["displayName"])
                    }
                })
            return matches
        except Exception as e:
            print(f"ESPN 抓取失敗: {e}")
            return []

    def fetch_bet365_odds(self):
        """抓取 Bet365 賠率（透過 The Odds API）"""
        try:
            url = "https://api.the-odds-api.com/v4/sports/soccer_world_cup/odds"
            params = {
                "apiKey": self.odds_api_key,
                "regions": "uk",
                "markets": "h2h,totals",
                "oddsFormat": "decimal"
            }
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                for event in resp.json():
                    for book in event.get("bookmakers", []):
                        if book["key"] == "bet365":
                            return {
                                "home_win": book["markets"][0]["outcomes"][0].get("price", "-"),
                                "draw": book["markets"][0]["outcomes"][1].get("price", "-"),
                                "away_win": book["markets"][0]["outcomes"][2].get("price", "-"),
                                "over": book.get("markets", [{}])[1].get("outcomes", [{}])[0].get("price", "-"),
                                "under": book.get("markets", [{}])[1].get("outcomes", [{}])[1].get("price", "-")
                            }
            return None
        except:
            return None

    def update_all(self):
        """完整更新所有數據"""
        print("🚀 開始更新多聯賽數據...")

        # NBA Summer League
        self.data["matches"].extend(self.fetch_espn_scores("basketball/nba"))

        # WNBA
        self.data["matches"].extend(self.fetch_espn_scores("basketball/wnba"))

        # 世界盃足球 + Bet365
        football = self.fetch_espn_scores("soccer/fifa.world")
        for match in football:
            match["bet365_odds"] = self.fetch_bet365_odds()
            self.data["matches"].append(match)

        # 儲存
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

        print(f"✅ 更新完成！共 {len(self.data['matches'])} 場比賽")
        print(f"更新時間: {self.data['last_update']}")
        return self.data


if __name__ == "__main__":
    updater = DataUpdater()
    updater.update_all()
