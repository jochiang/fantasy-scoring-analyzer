"""
Data loader for nflverse data.
Fetches and caches seasonal stats, play-by-play, and roster data.
Uses nflreadpy (replacement for archived nfl-data-py).
"""

import nflreadpy as nfl
import pandas as pd
from pathlib import Path

CACHE_DIR = Path(__file__).parent.parent / "cache"


def ensure_cache_dir():
    """Create cache directory if it doesn't exist."""
    CACHE_DIR.mkdir(exist_ok=True)


def load_seasonal_stats(year: int, use_cache: bool = True) -> pd.DataFrame:
    """
    Load seasonal player stats from nflverse.

    Args:
        year: NFL season year
        use_cache: Whether to use cached data if available

    Returns:
        DataFrame with seasonal player stats
    """
    ensure_cache_dir()
    cache_file = CACHE_DIR / f"seasonal_stats_{year}.parquet"

    if use_cache and cache_file.exists():
        return pd.read_parquet(cache_file)

    # nflreadpy uses load_player_stats with summary_level for seasonal data
    # Returns Polars DataFrame, convert to pandas
    stats = nfl.load_player_stats(year, summary_level="reg+post").to_pandas()
    stats.to_parquet(cache_file)
    return stats


def load_pbp_data(year: int, use_cache: bool = True) -> pd.DataFrame:
    """
    Load play-by-play data from nflverse.

    Args:
        year: NFL season year
        use_cache: Whether to use cached data if available

    Returns:
        DataFrame with play-by-play data
    """
    ensure_cache_dir()
    cache_file = CACHE_DIR / f"pbp_{year}.parquet"

    if use_cache and cache_file.exists():
        return pd.read_parquet(cache_file)

    # nflreadpy returns Polars DataFrame, convert to pandas
    pbp = nfl.load_pbp(year).to_pandas()
    pbp.to_parquet(cache_file)
    return pbp


def load_rosters(year: int, use_cache: bool = True) -> pd.DataFrame:
    """
    Load roster data from nflverse.

    Args:
        year: NFL season year
        use_cache: Whether to use cached data if available

    Returns:
        DataFrame with roster/player info
    """
    ensure_cache_dir()
    cache_file = CACHE_DIR / f"rosters_{year}.parquet"

    if use_cache and cache_file.exists():
        return pd.read_parquet(cache_file)

    # nflreadpy returns Polars DataFrame, convert to pandas
    rosters = nfl.load_rosters(year).to_pandas()
    rosters.to_parquet(cache_file)
    return rosters


def get_player_stats_with_info(year: int, use_cache: bool = True) -> pd.DataFrame:
    """
    Load seasonal stats merged with player info (name, team, position).

    Args:
        year: NFL season year
        use_cache: Whether to use cached data if available

    Returns:
        DataFrame with stats and player info
    """
    stats = load_seasonal_stats(year, use_cache)
    rosters = load_rosters(year, use_cache)

    # Get unique player info from rosters (take latest entry per player)
    player_info = rosters.sort_values('week').groupby('player_id').last().reset_index()
    player_info = player_info[['player_id', 'player_name', 'position', 'team']]

    # Merge stats with player info
    merged = stats.merge(player_info, on='player_id', how='left')

    # Filter to offensive skill positions only
    skill_positions = ['QB', 'RB', 'WR', 'TE']
    merged = merged[merged['position'].isin(skill_positions)]

    return merged


def clear_cache():
    """Clear all cached data files."""
    if CACHE_DIR.exists():
        for f in CACHE_DIR.glob("*.parquet"):
            f.unlink()
