# Fantasy Scoring Analyzer

An interactive tool to analyze how different fantasy football scoring settings affect player rankings.

## Quick Start

```bash
cd fantasy-scoring-analyzer
uv init
uv add nfl-data-py pandas streamlit
streamlit run src/app.py
```

## What This Does

- Interactive Streamlit UI with sliders for each scoring category
- See rankings update dynamically as you adjust settings
- Position rankings: Top 12 QB, Top 24 RB/WR, Top 12 TE
- Risers/Fallers comparison vs Yahoo Standard baseline
- Preset buttons for Standard, PPR, Half-PPR configs

## Data Source

Uses **nflverse** (`nfl-data-py`) - free, comprehensive NFL data with no rate limits.
- Data cached locally via `@st.cache_data` so API calls only happen once per session

## Implementation

See `PLAN.md` for full implementation details.

## Created

2025-12-29 - Research session on NFL APIs for fantasy football analysis.
