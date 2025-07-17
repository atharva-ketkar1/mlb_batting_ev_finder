import pandas as pd
import os
import re
from datetime import datetime
from glob import glob
from pybaseball import batting_stats_range
import unicodedata

def normalize_name(name: str) -> str:
    if pd.isna(name):
        return ""
    n = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    n = n.lower().strip()
    n = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b\.?", "", n)
    n = re.sub(r"\s*\([^)]*\)", "", n)
    return re.sub(r"\s+", " ", n).strip()

def fetch_actual_batter_stats(slate_date):
    try:
        logs = batting_stats_range(slate_date, slate_date)
    except Exception as e:
        print(f"Failed to fetch batter stats for {slate_date}: {e}")
        return {}

    logs['player_norm'] = logs['Name'].apply(normalize_name)
    logs['hrr'] = logs['H'] + logs['R'] + logs['RBI']
    return logs.set_index('player_norm')['hrr'].to_dict()

def evaluate_batter_file(path):
    df_check = pd.read_csv(path)
    if 'Result' in df_check.columns or any(df_check['player'].astype(str).str.startswith('SUMMARY:')):
        print(f"Skipping {os.path.basename(path)} — already evaluated.")
        return
    
    m = re.search(r"best_batter_picks_(\d{4}-\d{2}-\d{2})\.csv$", path)
    if not m:
        return
    slate_date = m.group(1)

    if slate_date >= datetime.today().strftime("%Y-%m-%d"):
        print(f"Skipping {os.path.basename(path)} — game may not be finished.")
        return

    df_check = pd.read_csv(path)
    if 'Result' in df_check.columns and df_check['Result'].notna().all():
        print(f"Already evaluated {os.path.basename(path)}")
        return

    print(f"Evaluating {os.path.basename(path)} for {slate_date}")
    actual = fetch_actual_batter_stats(slate_date)
    if not actual:
        return

    df = df_check.copy()
    actual_hrr = []
    results = []

    for _, row in df.iterrows():
        pn = normalize_name(row['player'])
        total = actual.get(pn, None)
        actual_hrr.append(total)

        line = row.get('prizepicks_line')
        pick = row.get('suggestion')

        if total is None or pd.isna(line) or pick not in ('OVER', 'UNDER'):
            results.append('')
        else:
            if total == line:
                results.append('PUSH')
            elif pick == 'OVER':
                results.append('HIT' if total > line else 'MISS')
            else:
                results.append('HIT' if total < line else 'MISS')

    df['Actual_HRR'] = actual_hrr
    df['Result'] = results

    num_hit = results.count('HIT')
    num_miss = results.count('MISS')
    num_push = results.count('PUSH')
    num_total = num_hit + num_miss
    hit_rate = (num_hit / num_total) * 100 if num_total > 0 else 0

    summary_row = {
        'player': f'SUMMARY: {num_hit}/{num_total} - {hit_rate:.1f}%',
        'team': '',
        'stat_type': '',
        'prizepicks_line': '',
        'over_odds_ud': '',
        'under_odds_ud': '',
        'dk_odds_over': '',
        'dk_odds_under': '',
        'max_edge': '',
        'suggestion': '',
        'Actual_HRR': '',
        'Result': f'HITS: {num_hit}, MISSES: {num_miss}, PUSHES: {num_push}'
    }

    df = pd.concat([df, pd.DataFrame([summary_row])], ignore_index=True)
    df.to_csv(path, index=False)
    print(f"Updated: {path} — {num_hit}/{num_total} HITS ({hit_rate:.1f}%)\n")

def main():
    files = glob("best_picks/best_batter_picks_*.csv")
    for f in sorted(files):
        evaluate_batter_file(f)

if __name__ == "__main__":
    main()
