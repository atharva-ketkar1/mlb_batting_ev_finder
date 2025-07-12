import requests
import pandas as pd

def scrape_draftkings_mlb():
    url = "https://sportsbook-nash.draftkings.com/api/sportscontent/dkusil/v1/leagues/84240/categories/743/subcategories/17406"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        "Referer": "https://sportsbook.draftkings.com/",
        "Origin": "https://sportsbook.draftkings.com",
        "Accept": "*/*",
    }

    response = requests.get(url, headers=headers)
    data = response.json()

    market_map = {m['id']: m for m in data['markets']}

    player_line_odds = {}

    for sel in data['selections']:
        market = market_map.get(sel['marketId'], {})
        market_name = market.get('name', '')

        if 'Hits + Runs + RBIs O/U' not in market_name:
            continue

        participants = sel.get('participants', [])
        if not participants:
            continue

        player = participants[0]['name']
        line = sel.get('points', None)  
        if line is None:
            continue

        label = sel.get('label', '').lower()  
        odds_raw = sel.get('displayOdds', {}).get('american', None)

        key = (player, line)
        if key not in player_line_odds:
            player_line_odds[key] = {'over': None, 'under': None}

        if label == 'over':
            player_line_odds[key]['over'] = odds_raw
        elif label == 'under':
            player_line_odds[key]['under'] = odds_raw

    # Convert dict to list of dicts for DataFrame
    rows = []
    for (player, line), odds_dict in player_line_odds.items():
        rows.append({
            "player": player,
            "dk_line": line,
            "dk_odds_over": odds_dict['over'],
            "dk_odds_under": odds_dict['under'],
        })

    return pd.DataFrame(rows)

if __name__ == "__main__":
    df = scrape_draftkings_mlb()
    print(df)