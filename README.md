# mlb_batting_ev_finder

## Overview

**`mlb_batting_ev_finder`** is a data-driven tool for identifying profitable MLB hitter prop bets for *Hits + Runs + RBIs (HRR)* — on **PrizePicks**. It scrapes prop lines and odds from multiple sportsbooks and computes the expected value (EV) of each pick to surface the best betting opportunities.

---

## What It Does

The script performs the following:

1. **Scrapes props and odds** from:
   - **PrizePicks** (Hits+Runs+RBI line for each player)
   - **DraftKings** (Over/Under odds for the Hits+Runs+RBI line)
   - **Underdog Fantasy** (Over/Under odds for the Hits+Runs+RBI line)

3. **Uses No Vig Probabilities**, to optimize accuracy instead of traditional American odds.

4. **Calculates EV edges** based on a standard breakeven probability of 0.5238. On Prizepicks this would be a 2-man flex breakeven probability. Nobody does 2-man flexes, but I didn't want to increase the breakeven probability too much, or the edges would seem incredibly low.

5. **Ranks player props** by max EV edge and suggests a bet (`OVER` or `UNDER`) for each line.

6. **Outputs Results** in the `best_picks/best_batter_picks{current-date}.csv`: top picks with the highest EV edges and betting recommendations at the time of pushing to the repo.

---
