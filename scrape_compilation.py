from datetime import datetime
from scrapes.scrape_prizepicks import scrape_prizepicks_mlb
from scrapes.scrape_draftkings import scrape_draftkings_mlb
from scrapes.scrape_underdog import scrape_underdog_mlb
import pandas as pd
import unicodedata
import re

def fix_escaped_unicode(text):
    if pd.isna(text):
        return ""
    try:
        return bytes(text, "utf-8").decode("unicode_escape").encode("latin1").decode("utf-8")
    except Exception:
        return text

def normalize_name(name: str) -> str:
    if pd.isna(name):
        return ""
    n = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    n = n.lower().strip()
    n = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b\.?", "", n)
    n = re.sub(r"\s*\([^)]*\)", "", n)
    return re.sub(r"\s+", " ", n).strip()

def american_to_prob(odds):
    try:
        odds_str = str(odds).replace('−', '-')
        odds_int = int(odds_str)
        if odds_int > 0:
            return 100 / (odds_int + 100)
        else:
            return abs(odds_int) / (abs(odds_int) + 100)
    except Exception:
        return None

def no_vig_probs(over_odds, under_odds):
    try:
        p_over = american_to_prob(over_odds)
        p_under = american_to_prob(under_odds)
        total = p_over + p_under
        if total == 0:
            return None, None
        return p_over / total, p_under / total
    except:
        return None, None

def calc_edge(prob, breakeven=0.5238):
    if prob is None:
        return None
    return prob - breakeven

def scrape_all():
    df_pp = scrape_prizepicks_mlb()
    df_dk = scrape_draftkings_mlb()
    df_ud = scrape_underdog_mlb()

    df_pp["player"] = df_pp["player"].apply(fix_escaped_unicode).apply(normalize_name)
    df_dk["player"] = df_dk["player"].apply(fix_escaped_unicode).apply(normalize_name)
    df_ud["player"] = df_ud["player"].apply(fix_escaped_unicode).apply(normalize_name)

    df_pp["prizepicks_line"] = df_pp["prizepicks_line"].astype(float)
    df_dk["dk_line"] = df_dk["dk_line"].astype(float)
    df_ud["line_ud"] = df_ud["line_ud"].astype(float)

    return merge_dataframes(df_pp, df_dk, df_ud)

def merge_dataframes(df_pp, df_dk, df_ud):
    merged = pd.merge(
        df_pp,
        df_dk,
        how="left",
        left_on=["player", "prizepicks_line"],
        right_on=["player", "dk_line"]
    )

    merged = pd.merge(
        merged,
        df_ud,
        how="left",
        left_on=["player", "prizepicks_line"],
        right_on=["player", "line_ud"]
    )

    merged[['prob_over_dk', 'prob_under_dk']] = merged.apply(
    lambda row: pd.Series(no_vig_probs(row['dk_odds_over'], row['dk_odds_under'])),
    axis=1
    )

    merged[['prob_over_ud', 'prob_under_ud']] = merged.apply(
        lambda row: pd.Series(no_vig_probs(row['over_odds_ud'], row['under_odds_ud'])),
        axis=1
    )

    merged['edge_over_dk'] = merged['prob_over_dk'].apply(calc_edge)
    merged['edge_under_dk'] = merged['prob_under_dk'].apply(calc_edge)
    merged['edge_over_ud'] = merged['prob_over_ud'].apply(calc_edge)
    merged['edge_under_ud'] = merged['prob_under_ud'].apply(calc_edge)

    merged['edge_over_combined'] = merged.apply(
        lambda row: pd.Series([row['edge_over_dk'], row['edge_over_ud']]).dropna().mean(), axis=1
    )
    merged['edge_under_combined'] = merged.apply(
        lambda row: pd.Series([row['edge_under_dk'], row['edge_under_ud']]).dropna().mean(), axis=1
    )

    def best_bet(row):
        if pd.isna(row['edge_over_combined']) and pd.isna(row['edge_under_combined']):
            return 'N/A Both'
        if pd.isna(row['edge_over_combined']):
            return 'N/A Over'
        if pd.isna(row['edge_under_combined']):
            return 'N/A Under'
        return 'OVER' if row['edge_over_combined'] > row['edge_under_combined'] else 'UNDER'

    merged['suggestion'] = merged.apply(best_bet, axis=1)
    merged['max_edge'] = merged[['edge_over_combined', 'edge_under_combined']].max(axis=1)

    for col in ['prob_over_ud', 'prob_under_ud', 'prob_over_dk', 'prob_under_dk',
                'edge_over_ud', 'edge_under_ud', 'edge_over_dk', 'edge_under_dk',
                'edge_over_combined', 'edge_under_combined', 'max_edge']:
        if col in merged.columns:
            merged[col] = merged[col].round(3)

    merged = merged.sort_values(by='max_edge', ascending=False)

    return merged

if __name__ == "__main__":
    date = datetime.today().strftime('%Y-%m-%d')
    df = scrape_all()
    #df.to_csv("scraped_data_merge.csv", index=False)

    summary_df = df[['player', 'team', 'stat_type', 'prizepicks_line', 
                     'over_odds_ud', 'under_odds_ud', 'dk_odds_over', 'dk_odds_under', 
                     'max_edge', 'suggestion']].copy()
    summary_df = summary_df.sort_values(by='max_edge', ascending=False)

    summary_df.to_csv(f'best_picks/best_batter_picks_{date}.csv', index=False)
