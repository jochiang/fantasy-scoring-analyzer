# Fantasy Scoring Analyzer

## Goal

Build a tool that lets you modify fantasy football scoring settings (based on Yahoo's scoring categories) and see how player rankings shift across:
- Top 12/24/36 at each position (QB, RB, WR, TE)
- Top 120 overall players
- Excludes kickers and defense

## Data Source

**nflverse** via `nfl_data_py` (or the newer `nflreadpy`)
- GitHub: https://github.com/nflverse/nfl_data_py
- Docs: https://nflfastr.com/reference/calculate_player_stats.html
- Data available from 1999-present

### Why nflverse?
- Free, no rate limits
- Pre-aggregated player stats + full play-by-play
- Player IDs already parsed (unlike NFLsavant)
- Active community maintenance
- Python-ready

## Yahoo Scoring Categories to Support

### Passing
| Stat | Default | nflverse Source |
|------|---------|-----------------|
| Passing Yards | 25 yds/pt | `passing_yards` |
| Passing TDs | 4 pts | `passing_tds` |
| Interceptions | -1 | `interceptions` |
| Completions | 0 | `completions` |
| Passing Attempts | 0 | `attempts` |
| Incomplete Passes | 0 | `attempts - completions` |
| Times Sacked | 0 | `sacks` |
| 40+ Yd Completions | 0 | **Derive from PBP** |
| 40+ Yd Pass TDs | 0 | **Derive from PBP** |
| Pick Sixes | 0 | **Derive from PBP** |

### Rushing
| Stat | Default | nflverse Source |
|------|---------|-----------------|
| Rushing Yards | 10 yds/pt | `rushing_yards` |
| Rushing TDs | 6 pts | `rushing_tds` |
| Rushing Attempts | 0 pts | `carries` |
| 40+ Yd Rush | 0 pts | **Derive from PBP** |

### Receiving
| Stat | Default | nflverse Source |
|------|---------|-----------------|
| Receptions | 0 pts (0.5/1 PPR) | `receptions` |
| Receiving Yards | 10 yds/pt | `receiving_yards` |
| Receiving TDs | 6 pts | `receiving_tds` |
| 40+ Yd Receptions | 0 | **Derive from PBP** |
| 40+ Yd Rec TDs | 0 | **Derive from PBP** |

### Miscellaneous
| Stat | Default Pts | nflverse Source |
|------|-------------|-----------------|
| Fumbles | 0 | `rushing_fumbles + receiving_fumbles + sack_fumbles` |
| Fumbles Lost | -2 | `rushing_fumbles_lost + receiving_fumbles_lost + sack_fumbles_lost` |
| 2-PT Conversions | 2 | `passing_2pt_conversions + rushing_2pt_conversions + receiving_2pt_conversions` |
| Return Yards | 0 | **Derive from PBP** |
| Return TDs | 6 | `special_teams_tds` |
| Off Fumble Ret TD | 6 | **Derive from PBP** |

## Architecture

```
fantasy-scoring-analyzer/
├── PLAN.md                 # This file
├── pyproject.toml          # uv package config
├── src/
│   ├── __init__.py
│   ├── data_loader.py      # Fetch/cache nflverse data
│   ├── pbp_aggregator.py   # Derive 40+ yd plays, pick sixes, etc from PBP
│   ├── scorer.py           # Apply scoring rules to stats
│   ├── ranker.py           # Generate position/overall rankings
│   └── app.py              # Streamlit web interface
├── configs/
│   ├── yahoo_standard.json # Default Yahoo scoring
│   ├── yahoo_ppr.json      # PPR scoring
│   └── custom.json         # User-defined scoring
└── tests/
    └── test_scorer.py
```

## Implementation Steps

### Phase 1: Data Foundation
1. Set up uv project with dependencies (`nfl-data-py`, `pandas`, `streamlit`)
2. Create `data_loader.py`:
   - `load_seasonal_stats(year)` - fetch player season stats
   - `load_pbp_data(year)` - fetch play-by-play
   - Cache data locally to avoid re-fetching
3. Create `pbp_aggregator.py`:
   - Parse PBP for 40+ yard plays by player
   - Parse PBP for pick sixes
   - Parse PBP for return yards
   - Parse PBP for offensive fumble return TDs

### Phase 2: Scoring Engine
4. Create `scorer.py`:
   - Load scoring config from JSON
   - Calculate fantasy points per player
   - Convert yards-per-point to points-per-yard internally (e.g., 25 yds/pt → 0.04 pts/yd)
   - Support bonus scoring (e.g., +2 for 40+ yd TD)
   - Validate inputs: yardage as integers, other stats max 2 decimal places
5. Create scoring config JSONs for Yahoo standard/PPR

### Phase 3: Streamlit Interface
6. Create `ranker.py`:
   - Rank players by position (top 12/24/36)
   - Rank overall top 120
   - Compare two scoring configs to show risers/fallers
7. Create `app.py` (Streamlit):
   - Sidebar with sliders/inputs for each scoring category
   - Use `@st.cache_data` to cache nflverse API calls
   - Main panel with position ranking tables (QB, RB, WR, TE)
   - Risers/Fallers section comparing to baseline (e.g., Yahoo Standard)
   - Preset buttons to load common configs (Standard, PPR, Half-PPR)
8. Run with: `streamlit run src/app.py`

### Phase 4: Polish (Optional)
9. Add visualization (matplotlib/plotly charts of ranking changes)
10. Add multi-year analysis
11. Add CLI for batch comparisons (`click` library)
12. Export current settings to JSON

## Key nflverse Functions

```python
import nfl_data_py as nfl

# Seasonal player stats (aggregated)
stats = nfl.import_seasonal_data([2024])

# Play-by-play data (for deriving 40+ yd plays, etc)
pbp = nfl.import_pbp_data([2024])

# Player info (for names, positions, teams)
rosters = nfl.import_seasonal_rosters([2024])
```

## PBP Columns for Derived Stats

For 40+ yard plays, filter PBP where:
- `pass_length == 'deep'` or `yards_gained >= 40`
- `rush == 1` and `yards_gained >= 40`
- `complete_pass == 1` and `yards_gained >= 40`

For pick sixes:
- `interception == 1` and `return_touchdown == 1`

For return yards/TDs:
- `return_yards` column
- `return_touchdown == 1`

## Sample Scoring Config (JSON)

```json
{
  "name": "Yahoo PPR",
  "passing": {
    "passing_yards_per_point": 25,
    "passing_tds": 4,
    "interceptions": -1,
    "completions": 0,
    "attempts": 0,
    "sacks": 0,
    "pass_40_yd": 0,
    "pass_40_yd_td": 0,
    "pick_six": 0
  },
  "rushing": {
    "rushing_yards_per_point": 10,
    "rushing_tds": 6,
    "carries": 0,
    "rush_40_yd": 0
  },
  "receiving": {
    "receptions": 1,
    "receiving_yards_per_point": 10,
    "receiving_tds": 6,
    "rec_40_yd": 0,
    "rec_40_yd_td": 0
  },
  "misc": {
    "fumbles": 0,
    "fumbles_lost": -2,
    "two_pt_conversions": 2,
    "return_yards_per_point": 25,
    "return_tds": 6
  }
}
```

**Input Constraints:**
- Yardage stats: expressed as "yards per point" (integer, e.g., 25, 10)
- All other stats: max 2 decimal places (e.g., 0.25 PPR is valid, 0.251 is not)

## Streamlit UI Layout

```
┌─────────────────────────────────────────────────────────────────────────┐
│  SIDEBAR                          │  MAIN PANEL                         │
│                                   │                                     │
│  Year: [2024 ▼]                   │                                              │
│                                   │  TOP 12 QB                                   │
│  Presets:                         │  ┌──────────────────────────────────────────┐│
│  [Standard] [PPR] [Half-PPR]      │  │ Rk Player      Yds    TD  INT  Pts       ││
│                                   │  │ 1  J.Allen    4,306   40   6  425.2      ││
│  ─── Passing ───                  │  │ 2  L.Jackson  4,172   41   4  410.1      ││
│  Yards:    [===|===] 25 yds/pt    │  │ ...                                      ││
│  TDs:      [=====|=] 4 pts        │  └──────────────────────────────────────────┘│
│  INTs:     [|=======] -1 pts      │                                              │
│  40+ Comp: [|=======] 0 pts       │  TOP 24 RB                                   │
│                                   │  ┌──────────────────────────────────────────┐│
│  ─── Rushing ───                  │  │ Rk Player      Rush   Rec   TD   Pts     ││
│  Yards:    [===|===] 10 yds/pt    │  │ 1  S.Barkley  2,005   490   16  312.5    ││
│  TDs:      [======|] 6 pts        │  │ 2  D.Henry    1,921   331   18  298.2    ││
│  40+ Rush: [|=======] 0 pts       │  │ ...                                      ││
│                                   │  └──────────────────────────────────────────┘│
│  ─── Receiving ───                │                                              │
│  Receptions: [===|===] 0.5 pts    │  TOP 24 WR                                   │
│  Yards:    [===|===] 10 yds/pt    │  ┌──────────────────────────────────────────┐│
│  TDs:      [======|] 6 pts        │  │ Rk Player      Rec   Yds   TD   Pts      ││
│                                   │  │ 1  J.Chase     127  1,708  17  342.8     ││
│  ─── Misc ───                     │  │ 2  C.Lamb      101  1,479  12  265.9     ││
│  Fumbles Lost: [|====] -2 pts     │  │ ...                                      ││
│  2PT Conv:  [====|==] 2 pts       │  └──────────────────────────────────────────┘│
│                                   │                                              │
│                                   │  TOP 12 TE                                   │
│                                   │  ┌──────────────────────────────────────────┐│
│                                   │  │ Rk Player      Rec   Yds   TD   Pts      ││
│                                   │  │ 1  T.Kelce      93  1,020   9  178.0     ││
│                                   │  │ 2  S.LaPorta    86   965    8  162.5     ││
│                                   │  │ ...                                      ││
│                                   │  └──────────────────────────────────────────┘│
│                                   │                                              │
│                                   │  ─────────────────────────────────────────── │
│                                   │                                              │
│                                   │  RISERS vs Yahoo Standard                    │
│                                   │  ┌──────────────────────────────────────────┐│
│                                   │  │ D.Henry    RB  +7 (15 → 8)               ││
│                                   │  │ K.Williams RB  +5 (22 → 17)              ││
│                                   │  └──────────────────────────────────────────┘│
│                                   │                                              │
│                                   │  FALLERS vs Yahoo Standard                   │
│                                   │  ┌──────────────────────────────────────────┐│
│                                   │  │ P.Mahomes  QB  -4 (3 → 7)                ││
│                                   │  │ T.Hill     WR  -3 (8 → 11)               ││
│                                   │  └──────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────────────────┘
```

**Interaction Flow:**
1. Adjust any slider → rankings recalculate instantly
2. Click preset button → all sliders update to that config
3. Risers/Fallers always compare current settings vs Yahoo Standard baseline

## Notes

- nfl_data_py is deprecated in favor of nflreadpy, but still works
- Consider using nflreadpy if starting fresh
- Data is typically available ~24hrs after games
- Historical data back to 1999 for PBP, 1970 for basic stats

## Resources

- nflverse GitHub: https://github.com/nflverse
- nflfastR docs: https://nflfastr.com/
- Yahoo scoring reference: https://help.yahoo.com/kb/SLN6490.html
