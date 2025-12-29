"""
Play-by-play aggregator for deriving stats not in seasonal data.
Extracts 40+ yard plays, pick sixes, return yards, etc.
"""

import pandas as pd
from typing import Dict


def aggregate_pbp_stats(pbp: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate play-by-play data to get derived stats per player.

    Args:
        pbp: Play-by-play DataFrame from nflverse

    Returns:
        DataFrame with derived stats per player_id
    """
    results = {}

    # 40+ yard completions (passer)
    pass_40 = _count_40_yard_passes(pbp)
    results['pass_40_yd'] = pass_40

    # 40+ yard passing TDs (passer)
    pass_40_td = _count_40_yard_pass_tds(pbp)
    results['pass_40_yd_td'] = pass_40_td

    # Pick sixes thrown (passer - negative event)
    pick_sixes = _count_pick_sixes(pbp)
    results['pick_six'] = pick_sixes

    # 40+ yard rushes (rusher)
    rush_40 = _count_40_yard_rushes(pbp)
    results['rush_40_yd'] = rush_40

    # 40+ yard rush TDs (rusher)
    rush_40_td = _count_40_yard_rush_tds(pbp)
    results['rush_40_yd_td'] = rush_40_td

    # 40+ yard receptions (receiver)
    rec_40 = _count_40_yard_receptions(pbp)
    results['rec_40_yd'] = rec_40

    # 40+ yard receiving TDs (receiver)
    rec_40_td = _count_40_yard_rec_tds(pbp)
    results['rec_40_yd_td'] = rec_40_td

    # Combine all stats into one DataFrame
    combined = _combine_stats(results)
    return combined


def _count_40_yard_passes(pbp: pd.DataFrame) -> Dict[str, int]:
    """Count 40+ yard completions by passer."""
    mask = (
        (pbp['complete_pass'] == 1) &
        (pbp['yards_gained'] >= 40)
    )
    filtered = pbp[mask]
    return filtered.groupby('passer_player_id').size().to_dict()


def _count_40_yard_pass_tds(pbp: pd.DataFrame) -> Dict[str, int]:
    """Count 40+ yard passing TDs by passer."""
    mask = (
        (pbp['pass_touchdown'] == 1) &
        (pbp['yards_gained'] >= 40)
    )
    filtered = pbp[mask]
    return filtered.groupby('passer_player_id').size().to_dict()


def _count_pick_sixes(pbp: pd.DataFrame) -> Dict[str, int]:
    """Count pick sixes thrown by passer."""
    mask = (
        (pbp['interception'] == 1) &
        (pbp['return_touchdown'] == 1)
    )
    filtered = pbp[mask]
    return filtered.groupby('passer_player_id').size().to_dict()


def _count_40_yard_rushes(pbp: pd.DataFrame) -> Dict[str, int]:
    """Count 40+ yard rushes by rusher."""
    mask = (
        (pbp['rush_attempt'] == 1) &
        (pbp['yards_gained'] >= 40)
    )
    filtered = pbp[mask]
    return filtered.groupby('rusher_player_id').size().to_dict()


def _count_40_yard_rush_tds(pbp: pd.DataFrame) -> Dict[str, int]:
    """Count 40+ yard rush TDs by rusher."""
    mask = (
        (pbp['rush_touchdown'] == 1) &
        (pbp['yards_gained'] >= 40)
    )
    filtered = pbp[mask]
    return filtered.groupby('rusher_player_id').size().to_dict()


def _count_40_yard_receptions(pbp: pd.DataFrame) -> Dict[str, int]:
    """Count 40+ yard receptions by receiver."""
    mask = (
        (pbp['complete_pass'] == 1) &
        (pbp['yards_gained'] >= 40)
    )
    filtered = pbp[mask]
    return filtered.groupby('receiver_player_id').size().to_dict()


def _count_40_yard_rec_tds(pbp: pd.DataFrame) -> Dict[str, int]:
    """Count 40+ yard receiving TDs by receiver."""
    mask = (
        (pbp['pass_touchdown'] == 1) &
        (pbp['yards_gained'] >= 40)
    )
    filtered = pbp[mask]
    return filtered.groupby('receiver_player_id').size().to_dict()


def _combine_stats(stats_dict: Dict[str, Dict[str, int]]) -> pd.DataFrame:
    """Combine all stat dictionaries into a single DataFrame."""
    # Get all unique player IDs
    all_players = set()
    for stat_dict in stats_dict.values():
        all_players.update(stat_dict.keys())

    # Build DataFrame
    data = []
    for player_id in all_players:
        if pd.isna(player_id):
            continue
        row = {'player_id': player_id}
        for stat_name, stat_dict in stats_dict.items():
            row[stat_name] = stat_dict.get(player_id, 0)
        data.append(row)

    if not data:
        return pd.DataFrame(columns=['player_id'] + list(stats_dict.keys()))

    return pd.DataFrame(data)
