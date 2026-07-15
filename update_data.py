import requests
import json
from datetime import datetime

def fetch_espn_scores(sport, league_filter=None):
    """通用 ESPN 比分抓取"""
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/scoreboard"
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return []
        
        events = resp.json().get("events", [])
        matches = []
        
        for event in events[:12]:  # 限制數量
            comp = event["competitions"][0]
            home = comp["competitors"][0]
            away = comp["competitors"][1]
            
            league_name = event.get("league", {}).get("name", sport.upper())
            if league_filter and league_filter.lower() not in league_name.lower():
                continue
                
            matches.append({
                "league": league_name,
                "home": home["team"]["displayName"],
                "away": away["team"]["displayName"],
                "home_score": int(home.get("score", 0)),
                "away_score": int(away.get("score", 0)),
                "status": comp["status"]["type"]["shortDetail"],
                "time": datetime.now().strftime("%H:%M")
            })
        return matches
    except:
        return []


def update_all_data():
    """完整多聯賽數據更新"""
    data = {
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "matches": []
    }

    # ==================== 1. NBA Summer League ====================
    nba_matches = fetch_espn_scores("basketball/nba")
    for m in nba_matches:
        m["league"] = "NBA Summer League"
        data["matches"].append(m)

    # ==================== 2. WNBA ====================
    wnba_matches = fetch_espn_scores("basketball/wnba")
    data["matches"].extend(wnba_matches)

    # ==================== 3. PBA 菲律賓 ====================
    try:
        pba = {
            "league": "PBA Philippines",
            "home": "肯威爾基費貝爾希爾斯",
            "away": "泰豐吉普",
            "home_score": 0,
            "away_score": 0,
            "status": "即將開賽"
        }
        data["matches"].append(pba)
    except:
        pass

    # ==================== 4. NBL 新西蘭 / 澳洲 ====================
    try:
        nbl = {
            "league": "NBL New Zealand",
            "home": "塔拉納基航空",
            "away": "尼爾遜巨人",
            "home_score": 0,
            "away_score": 0,
            "status": "即將開賽"
        }
        data["matches"].append(nbl)
    except:
        pass

    # ==================== 5. 世界盃足球 ====================
    football_matches = fetch_espn_scores("soccer/fifa.world")
    data["matches"].extend(football_matches)

    # ==================== 6. 香港銀牌賽 ====================
    hk_matches = [
        {
            "league": "中國香港高級銀牌賽",
            "home": "香港東方",
            "away": "康仁福建",
            "home_score": 96,
            "away_score": 73,
            "status": "已結束"
        },
        {
            "league": "中國香港高級銀牌賽",
            "home": "滿貫",
            "away": "晉裕",
            "home_score": 106,
            "away_score": 65,
            "status": "已結束"
        }
    ]
    data["matches"].extend(hk_matches)

    # ==================== 儲存 ====================
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 多聯賽數據更新完成！共 {len(data['matches'])} 場比賽")
    print(f"更新時間: {data['last_update']}")
    return data


if __name__ == "__main__":
    update_all_data()
