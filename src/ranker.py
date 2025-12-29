"""
Player ranking engine.
Generates position and overall rankings, compares scoring configs.
"""

import pandas as pd
from typing import Dict, List, Tuple, Optional


# Position rank limits (top 36 for all positions)
POSITION_LIMITS = {
    'QB': 36,
    'RB': 36,
    'WR': 36,
    'TE': 36,
}

OVERALL_LIMIT = 120
POSITION_MEAN_LIMIT_36 = 36  # Calculate mean for top 36 at each position
POSITION_MEAN_LIMIT_12 = 12  # Calculate mean for top 12 at each position


def calculate_position_means(df: pd.DataFrame, limit: int = POSITION_MEAN_LIMIT_36) -> Dict[str, float]:
    """
    Calculate mean fantasy points for top N players at each position.

    Args:
        df: DataFrame with fantasy_points column
        limit: Number of top players to include in mean

    Returns:
        Dictionary of position -> mean fantasy points
    """
    means = {}
    for position in POSITION_LIMITS.keys():
        pos_df = df[df['position'] == position].copy()
        top_n = pos_df.nlargest(limit, 'fantasy_points')
        means[position] = round(top_n['fantasy_points'].mean(), 1) if len(top_n) > 0 else 0.0
    return means


def calculate_position_means_range(df: pd.DataFrame, start: int, end: int) -> Dict[str, float]:
    """
    Calculate mean fantasy points for players ranked start to end at each position.

    Args:
        df: DataFrame with fantasy_points column
        start: Starting rank (1-indexed, inclusive)
        end: Ending rank (1-indexed, inclusive)

    Returns:
        Dictionary of position -> mean fantasy points
    """
    means = {}
    for position in POSITION_LIMITS.keys():
        pos_df = df[df['position'] == position].copy()
        # Get top 'end' players, then slice from start-1 to end (0-indexed)
        top_n = pos_df.nlargest(end, 'fantasy_points')
        range_players = top_n.iloc[start-1:end]
        means[position] = round(range_players['fantasy_points'].mean(), 1) if len(range_players) > 0 else 0.0
    return means


def rank_by_position(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Rank players within each position.

    Args:
        df: DataFrame with fantasy_points column

    Returns:
        Dictionary of position -> ranked DataFrame
    """
    rankings = {}

    for position, limit in POSITION_LIMITS.items():
        pos_df = df[df['position'] == position].copy()
        pos_df = pos_df.sort_values('fantasy_points', ascending=False).head(limit)
        pos_df = pos_df.reset_index(drop=True)
        pos_df['rank'] = pos_df.index + 1
        rankings[position] = pos_df

    return rankings


def rank_overall(df: pd.DataFrame, limit: int = OVERALL_LIMIT) -> pd.DataFrame:
    """
    Rank all players overall.

    Args:
        df: DataFrame with fantasy_points column
        limit: Number of top players to return

    Returns:
        Ranked DataFrame
    """
    ranked = df.sort_values('fantasy_points', ascending=False).head(limit).copy()
    ranked = ranked.reset_index(drop=True)
    ranked['rank'] = ranked.index + 1
    return ranked


def compare_rankings(
    current_df: pd.DataFrame,
    baseline_df: pd.DataFrame,
    limit: int = OVERALL_LIMIT
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Compare two scoring systems to find risers and fallers.

    Args:
        current_df: DataFrame with current scoring fantasy_points
        baseline_df: DataFrame with baseline scoring fantasy_points
        limit: Number of top players to consider

    Returns:
        Tuple of (risers DataFrame, fallers DataFrame)
    """
    # Get overall rankings for both
    current_ranked = rank_overall(current_df, limit)
    baseline_ranked = rank_overall(baseline_df, limit)

    # Create rank lookup from baseline
    baseline_ranks = dict(zip(baseline_ranked['player_id'], baseline_ranked['rank']))

    # Calculate rank changes
    current_ranked['baseline_rank'] = current_ranked['player_id'].map(baseline_ranks)
    current_ranked['rank_change'] = current_ranked['baseline_rank'] - current_ranked['rank']

    # Players who weren't in baseline top N get NaN - fill with a high number
    current_ranked['baseline_rank'] = current_ranked['baseline_rank'].fillna(limit + 1)
    current_ranked['rank_change'] = current_ranked['rank_change'].fillna(0)

    # Sort by rank change
    risers = current_ranked[current_ranked['rank_change'] > 0].copy()
    risers = risers.sort_values('rank_change', ascending=False).head(10)

    fallers = current_ranked[current_ranked['rank_change'] < 0].copy()
    fallers = fallers.sort_values('rank_change', ascending=True).head(10)

    return risers, fallers


def get_position_stats_columns(position: str) -> List[str]:
    """
    Get the relevant stat columns to display for each position.

    Args:
        position: Player position (QB, RB, WR, TE)

    Returns:
        List of column names to display
    """
    if position == 'QB':
        return ['passing_yards', 'passing_tds', 'interceptions']
    elif position == 'RB':
        return ['rushing_yards', 'receiving_yards', 'rushing_tds', 'receiving_tds']
    elif position in ('WR', 'TE'):
        return ['receptions', 'receiving_yards', 'receiving_tds']
    else:
        return []


def format_position_table(
    df: pd.DataFrame,
    position: str,
    display_cols: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Format a position ranking table for display.

    Args:
        df: Ranked DataFrame for a position
        position: Player position
        display_cols: Optional list of columns to display

    Returns:
        Formatted DataFrame for display
    """
    if display_cols is None:
        display_cols = get_position_stats_columns(position)

    # Build display columns
    base_cols = ['rank', 'player_name', 'team']
    stat_cols = [c for c in display_cols if c in df.columns]
    final_cols = base_cols + stat_cols + ['fantasy_points']

    result = df[final_cols].copy()

    # Rename columns for display
    rename_map = {
        'player_name': 'Player',
        'team': 'Team',
        'rank': 'Rk',
        'fantasy_points': 'Pts',
        'passing_yards': 'Pass Yds',
        'passing_tds': 'Pass TD',
        'interceptions': 'INT',
        'rushing_yards': 'Rush Yds',
        'rushing_tds': 'Rush TD',
        'receiving_yards': 'Rec Yds',
        'receiving_tds': 'Rec TD',
        'receptions': 'Rec',
    }

    result = result.rename(columns=rename_map)

    return result


def format_risers_fallers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Format risers/fallers table for display.

    Args:
        df: DataFrame with rank_change column

    Returns:
        Formatted DataFrame for display
    """
    cols = ['player_name', 'position', 'rank_change', 'baseline_rank', 'rank']

    result = df[cols].copy()
    result['change_str'] = result.apply(
        lambda r: f"{'+' if r['rank_change'] > 0 else ''}{int(r['rank_change'])} ({int(r['baseline_rank'])} -> {int(r['rank'])})",
        axis=1
    )

    display_df = result[['player_name', 'position', 'change_str']].copy()
    display_df.columns = ['Player', 'Pos', 'Change']

    return display_df
