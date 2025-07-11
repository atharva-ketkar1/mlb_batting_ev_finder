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

def map_pp_line_to_dk_label(pp_line):
    try:
        return f"{int(float(pp_line)) + 1}+"
    except:
        return None

def american_to_prob(odds):
    try:
        odds = str(odds).replace('−', '-').replace('+', '')
        odds = int(odds)
        if odds > 0:
            return 100 / (odds + 100)
        else:
            return abs(odds) / (abs(odds) + 100)
    except:
        return None
    
def scrape_all():
    df_pp = scrape_prizepicks_mlb()
    df_dk = scrape_draftkings_mlb()
    df_ud = scrape_underdog_mlb()
    
    df_pp["player"] = df_pp["player"].apply(fix_escaped_unicode)
    df_dk["player"] = df_dk["player"].apply(fix_escaped_unicode)
    df_ud["player"] = df_ud["player"].apply(fix_escaped_unicode)
    
    df_pp["player"] = df_pp["player"].apply(normalize_name)
    df_dk["player"] = df_dk["player"].apply(normalize_name)
    df_ud["player"] = df_ud["player"].apply(normalize_name)
    
    df_pp["dk_label"] = df_pp["prizepicks_line"].apply(map_pp_line_to_dk_label)
    df_ud["line_ud"] = df_ud["line_ud"].astype(float)
    
    return merge_dataframes(df_pp, df_dk, df_ud)
    
def merge_dataframes(df_pp, df_dk, df_ud):
    
    merged = pd.merge(
        df_pp,
        df_dk,
        how="left",
        on=["player", "dk_label"]
    )

    merged = pd.merge(
        merged,
        df_ud,
        how="left",
        left_on=["player", "prizepicks_line"],
        right_on=["player", "line_ud"]
    )
    
    return merged



if __name__ == "__main__":
    #df = scrape_all()
    #df.to_csv("scraped_data.csv", index=False)
    #print(df)
    print('hello')