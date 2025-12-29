"""
Fantasy scoring engine.
Calculates fantasy points based on configurable scoring settings.
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class ScoringConfig:
    """Fantasy scoring configuration."""
    name: str = "Custom"

    # Passing (yards expressed as yards-per-point)
    passing_yards_per_point: int = 25  # 25 yards = 1 point
    passing_tds: float = 4.0
    interceptions: float = -1.0
    completions: float = 0.0
    attempts: float = 0.0
    sacks: float = 0.0
    pass_40_yd: float = 0.0
    pass_40_yd_td: float = 0.0
    pick_six: float = 0.0

    # Rushing (yards expressed as yards-per-point)
    rushing_yards_per_point: int = 10  # 10 yards = 1 point
    rushing_tds: float = 6.0
    carries: float = 0.0
    rush_40_yd: float = 0.0
    rush_40_yd_td: float = 0.0

    # Receiving (yards expressed as yards-per-point)
    receptions: float = 0.0  # 0 for standard, 0.5 for half-PPR, 1 for full PPR
    receiving_yards_per_point: int = 10  # 10 yards = 1 point
    receiving_tds: float = 6.0
    rec_40_yd: float = 0.0
    rec_40_yd_td: float = 0.0

    # Misc
    fumbles: float = 0.0
    fumbles_lost: float = -2.0
    two_pt_conversions: float = 2.0
    return_yards_per_point: int = 0  # 0 means no points for return yards
    return_tds: float = 6.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "passing": {
                "passing_yards_per_point": self.passing_yards_per_point,
                "passing_tds": self.passing_tds,
                "interceptions": self.interceptions,
                "completions": self.completions,
                "attempts": self.attempts,
                "sacks": self.sacks,
                "pass_40_yd": self.pass_40_yd,
                "pass_40_yd_td": self.pass_40_yd_td,
                "pick_six": self.pick_six,
            },
            "rushing": {
                "rushing_yards_per_point": self.rushing_yards_per_point,
                "rushing_tds": self.rushing_tds,
                "carries": self.carries,
                "rush_40_yd": self.rush_40_yd,
                "rush_40_yd_td": self.rush_40_yd_td,
            },
            "receiving": {
                "receptions": self.receptions,
                "receiving_yards_per_point": self.receiving_yards_per_point,
                "receiving_tds": self.receiving_tds,
                "rec_40_yd": self.rec_40_yd,
                "rec_40_yd_td": self.rec_40_yd_td,
            },
            "misc": {
                "fumbles": self.fumbles,
                "fumbles_lost": self.fumbles_lost,
                "two_pt_conversions": self.two_pt_conversions,
                "return_yards_per_point": self.return_yards_per_point,
                "return_tds": self.return_tds,
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScoringConfig":
        """Create from dictionary."""
        config = cls(name=data.get("name", "Custom"))

        if "passing" in data:
            p = data["passing"]
            config.passing_yards_per_point = p.get("passing_yards_per_point", 25)
            config.passing_tds = p.get("passing_tds", 4.0)
            config.interceptions = p.get("interceptions", -1.0)
            config.completions = p.get("completions", 0.0)
            config.attempts = p.get("attempts", 0.0)
            config.sacks = p.get("sacks", 0.0)
            config.pass_40_yd = p.get("pass_40_yd", 0.0)
            config.pass_40_yd_td = p.get("pass_40_yd_td", 0.0)
            config.pick_six = p.get("pick_six", 0.0)

        if "rushing" in data:
            r = data["rushing"]
            config.rushing_yards_per_point = r.get("rushing_yards_per_point", 10)
            config.rushing_tds = r.get("rushing_tds", 6.0)
            config.carries = r.get("carries", 0.0)
            config.rush_40_yd = r.get("rush_40_yd", 0.0)
            config.rush_40_yd_td = r.get("rush_40_yd_td", 0.0)

        if "receiving" in data:
            rec = data["receiving"]
            config.receptions = rec.get("receptions", 0.0)
            config.receiving_yards_per_point = rec.get("receiving_yards_per_point", 10)
            config.receiving_tds = rec.get("receiving_tds", 6.0)
            config.rec_40_yd = rec.get("rec_40_yd", 0.0)
            config.rec_40_yd_td = rec.get("rec_40_yd_td", 0.0)

        if "misc" in data:
            m = data["misc"]
            config.fumbles = m.get("fumbles", 0.0)
            config.fumbles_lost = m.get("fumbles_lost", -2.0)
            config.two_pt_conversions = m.get("two_pt_conversions", 2.0)
            config.return_yards_per_point = m.get("return_yards_per_point", 0)
            config.return_tds = m.get("return_tds", 6.0)

        return config

    @classmethod
    def from_json(cls, path: Path) -> "ScoringConfig":
        """Load from JSON file."""
        with open(path) as f:
            data = json.load(f)
        return cls.from_dict(data)

    def save_json(self, path: Path):
        """Save to JSON file."""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


def validate_scoring_value(value: float, is_yardage: bool = False) -> float:
    """
    Validate a scoring value.

    Args:
        value: The value to validate
        is_yardage: If True, must be integer; if False, max 2 decimal places

    Returns:
        Validated value

    Raises:
        ValueError: If validation fails
    """
    if is_yardage:
        if value != int(value):
            raise ValueError(f"Yardage values must be integers, got {value}")
        return int(value)
    else:
        # Round to 2 decimal places
        return round(value, 2)


def calculate_fantasy_points(
    stats: pd.DataFrame,
    pbp_stats: Optional[pd.DataFrame],
    config: ScoringConfig
) -> pd.DataFrame:
    """
    Calculate fantasy points for each player.

    Args:
        stats: Seasonal stats DataFrame with player info
        pbp_stats: PBP-derived stats DataFrame (optional)
        config: Scoring configuration

    Returns:
        DataFrame with fantasy points added
    """
    df = stats.copy()

    # Merge PBP stats if provided
    if pbp_stats is not None and not pbp_stats.empty:
        df = df.merge(pbp_stats, on='player_id', how='left')
        # Fill NaN PBP stats with 0
        pbp_cols = [c for c in pbp_stats.columns if c != 'player_id']
        df[pbp_cols] = df[pbp_cols].fillna(0)

    # Initialize fantasy points
    df['fantasy_points'] = 0.0

    # Passing points
    if 'passing_yards' in df.columns and config.passing_yards_per_point > 0:
        df['fantasy_points'] += df['passing_yards'].fillna(0) / config.passing_yards_per_point

    if 'passing_tds' in df.columns:
        df['fantasy_points'] += df['passing_tds'].fillna(0) * config.passing_tds

    if 'interceptions' in df.columns:
        df['fantasy_points'] += df['interceptions'].fillna(0) * config.interceptions

    if 'completions' in df.columns:
        df['fantasy_points'] += df['completions'].fillna(0) * config.completions

    if 'attempts' in df.columns:
        df['fantasy_points'] += df['attempts'].fillna(0) * config.attempts

    if 'sacks' in df.columns:
        df['fantasy_points'] += df['sacks'].fillna(0) * config.sacks

    # PBP-derived passing stats
    if 'pass_40_yd' in df.columns:
        df['fantasy_points'] += df['pass_40_yd'].fillna(0) * config.pass_40_yd

    if 'pass_40_yd_td' in df.columns:
        df['fantasy_points'] += df['pass_40_yd_td'].fillna(0) * config.pass_40_yd_td

    if 'pick_six' in df.columns:
        df['fantasy_points'] += df['pick_six'].fillna(0) * config.pick_six

    # Rushing points
    if 'rushing_yards' in df.columns and config.rushing_yards_per_point > 0:
        df['fantasy_points'] += df['rushing_yards'].fillna(0) / config.rushing_yards_per_point

    if 'rushing_tds' in df.columns:
        df['fantasy_points'] += df['rushing_tds'].fillna(0) * config.rushing_tds

    if 'carries' in df.columns:
        df['fantasy_points'] += df['carries'].fillna(0) * config.carries

    # PBP-derived rushing stats
    if 'rush_40_yd' in df.columns:
        df['fantasy_points'] += df['rush_40_yd'].fillna(0) * config.rush_40_yd

    if 'rush_40_yd_td' in df.columns:
        df['fantasy_points'] += df['rush_40_yd_td'].fillna(0) * config.rush_40_yd_td

    # Receiving points
    if 'receptions' in df.columns:
        df['fantasy_points'] += df['receptions'].fillna(0) * config.receptions

    if 'receiving_yards' in df.columns and config.receiving_yards_per_point > 0:
        df['fantasy_points'] += df['receiving_yards'].fillna(0) / config.receiving_yards_per_point

    if 'receiving_tds' in df.columns:
        df['fantasy_points'] += df['receiving_tds'].fillna(0) * config.receiving_tds

    # PBP-derived receiving stats
    if 'rec_40_yd' in df.columns:
        df['fantasy_points'] += df['rec_40_yd'].fillna(0) * config.rec_40_yd

    if 'rec_40_yd_td' in df.columns:
        df['fantasy_points'] += df['rec_40_yd_td'].fillna(0) * config.rec_40_yd_td

    # Misc points
    # Fumbles (total)
    fumble_cols = ['rushing_fumbles', 'receiving_fumbles', 'sack_fumbles']
    total_fumbles = sum(df[c].fillna(0) for c in fumble_cols if c in df.columns)
    df['fantasy_points'] += total_fumbles * config.fumbles

    # Fumbles lost
    fumble_lost_cols = ['rushing_fumbles_lost', 'receiving_fumbles_lost', 'sack_fumbles_lost']
    total_fumbles_lost = sum(df[c].fillna(0) for c in fumble_lost_cols if c in df.columns)
    df['fantasy_points'] += total_fumbles_lost * config.fumbles_lost

    # 2-point conversions
    two_pt_cols = ['passing_2pt_conversions', 'rushing_2pt_conversions', 'receiving_2pt_conversions']
    total_2pt = sum(df[c].fillna(0) for c in two_pt_cols if c in df.columns)
    df['fantasy_points'] += total_2pt * config.two_pt_conversions

    # Return TDs
    if 'special_teams_tds' in df.columns:
        df['fantasy_points'] += df['special_teams_tds'].fillna(0) * config.return_tds

    # Round to 1 decimal place
    df['fantasy_points'] = df['fantasy_points'].round(1)

    return df


# Preset configurations
def get_yahoo_standard() -> ScoringConfig:
    """Get Yahoo Standard scoring configuration."""
    return ScoringConfig(
        name="Yahoo Standard",
        passing_yards_per_point=25,
        passing_tds=4,
        interceptions=-1,
        rushing_yards_per_point=10,
        rushing_tds=6,
        receptions=0,
        receiving_yards_per_point=10,
        receiving_tds=6,
        fumbles_lost=-2,
        two_pt_conversions=2,
        return_tds=6,
    )


def get_yahoo_ppr() -> ScoringConfig:
    """Get Yahoo PPR scoring configuration."""
    config = get_yahoo_standard()
    config.name = "Yahoo PPR"
    config.receptions = 1.0
    return config


def get_yahoo_half_ppr() -> ScoringConfig:
    """Get Yahoo Half-PPR scoring configuration."""
    config = get_yahoo_standard()
    config.name = "Yahoo Half-PPR"
    config.receptions = 0.5
    return config
