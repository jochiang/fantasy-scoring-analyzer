"""Tests for the scoring engine."""

import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from scorer import ScoringConfig, calculate_fantasy_points, get_yahoo_standard


def test_scoring_config_defaults():
    """Test default scoring config values."""
    config = ScoringConfig()
    assert config.passing_yards_per_point == 25
    assert config.passing_tds == 4.0
    assert config.rushing_yards_per_point == 10
    assert config.rushing_tds == 6.0
    assert config.receptions == 0.0


def test_yahoo_standard_preset():
    """Test Yahoo Standard preset."""
    config = get_yahoo_standard()
    assert config.name == "Yahoo Standard"
    assert config.passing_yards_per_point == 25
    assert config.receptions == 0.0


def test_config_to_dict_roundtrip():
    """Test config serialization roundtrip."""
    original = ScoringConfig(name="Test", receptions=0.5)
    data = original.to_dict()
    restored = ScoringConfig.from_dict(data)
    assert restored.name == "Test"
    assert restored.receptions == 0.5


def test_calculate_fantasy_points():
    """Test fantasy point calculation."""
    # Create mock player data
    stats = pd.DataFrame({
        'player_id': ['p1', 'p2'],
        'player_name': ['Player 1', 'Player 2'],
        'position': ['QB', 'RB'],
        'team': ['NYG', 'DAL'],
        'passing_yards': [4000, 0],
        'passing_tds': [30, 0],
        'interceptions': [10, 0],
        'rushing_yards': [200, 1500],
        'rushing_tds': [5, 12],
        'receptions': [0, 50],
        'receiving_yards': [0, 400],
        'receiving_tds': [0, 3],
    })

    config = get_yahoo_standard()
    result = calculate_fantasy_points(stats, None, config)

    assert 'fantasy_points' in result.columns
    assert len(result) == 2

    # QB: 4000/25 + 30*4 + 10*(-1) + 200/10 + 5*6 = 160 + 120 - 10 + 20 + 30 = 320
    qb_pts = result[result['player_id'] == 'p1']['fantasy_points'].iloc[0]
    assert qb_pts == 320.0

    # RB: 1500/10 + 12*6 + 50*0 + 400/10 + 3*6 = 150 + 72 + 0 + 40 + 18 = 280
    rb_pts = result[result['player_id'] == 'p2']['fantasy_points'].iloc[0]
    assert rb_pts == 280.0


def test_ppr_scoring():
    """Test PPR scoring adds reception points."""
    stats = pd.DataFrame({
        'player_id': ['p1'],
        'player_name': ['Player 1'],
        'position': ['WR'],
        'team': ['NYG'],
        'receptions': [100],
        'receiving_yards': [1000],
        'receiving_tds': [10],
    })

    # Standard (no PPR)
    standard = get_yahoo_standard()
    result_std = calculate_fantasy_points(stats, None, standard)
    pts_std = result_std['fantasy_points'].iloc[0]

    # PPR
    ppr = ScoringConfig(receptions=1.0)
    result_ppr = calculate_fantasy_points(stats, None, ppr)
    pts_ppr = result_ppr['fantasy_points'].iloc[0]

    # PPR should have 100 more points (1 pt per reception)
    assert pts_ppr - pts_std == 100.0


if __name__ == "__main__":
    test_scoring_config_defaults()
    test_yahoo_standard_preset()
    test_config_to_dict_roundtrip()
    test_calculate_fantasy_points()
    test_ppr_scoring()
    print("All tests passed!")
