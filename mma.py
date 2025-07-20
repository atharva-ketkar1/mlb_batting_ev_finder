import requests
import pandas as pd

# Desired stats for UFC
DESIRED_STATS = ["Significant Strikes"]

def scrape_prizepicks_mma():
    url = "https://api.prizepicks.com/projections"
    params = {"league_id": "12", "per_page": "250"}  # UFC is league_id 12
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, params=params, headers=headers)
    data = response.json()

    projections = data["data"]
    included = {item["id"]: item for item in data.get("included", [])}

    all_records = []
    for proj in projections:
        attr = proj["attributes"]
        stat_type = attr.get("stat_display_name", "")  # use display name for readability
        line_score = attr.get("line_score")
        odds_type = attr.get("odds_type", "none")

        if odds_type != "standard" or stat_type not in DESIRED_STATS:
            continue

        player_id = str(proj["relationships"]["new_player"]["data"]["id"])
        player_info = included.get(player_id, {}).get("attributes", {})
        name = player_info.get("name") or attr.get("description", "Unknown")
        team = player_info.get("team", "N/A")

        all_records.append({
            "player": name,
            "prizepicks_line": line_score,
        })

    return pd.DataFrame(all_records)

if __name__ == "__main__":
    print(scrape_prizepicks_mma())
