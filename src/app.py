"""
Streamlit app for Fantasy Scoring Analyzer.
Interactive UI to explore how scoring settings affect player rankings.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from data_loader import load_seasonal_stats, load_pbp_data
from pbp_aggregator import aggregate_pbp_stats
from scorer import ScoringConfig, calculate_fantasy_points, get_yahoo_standard
from ranker import (
    rank_by_position,
    rank_overall,
    compare_rankings,
    format_position_table,
    format_risers_fallers,
    calculate_position_means,
    calculate_position_means_range,
    POSITION_LIMITS,
    POSITION_MEAN_LIMIT_12,
    POSITION_MEAN_LIMIT_36,
)


st.set_page_config(
    page_title="Fantasy Scoring Analyzer",
    page_icon="🏈",
    layout="wide",
)

st.title("Fantasy Scoring Analyzer")


# Initialize session state with defaults if not already set
def init_session_state():
    defaults = {
        'passing_yards_per_point': 25,
        'passing_tds': 4.0,
        'interceptions': -1.0,
        'completions': 0.0,
        'pass_40_yd': 0.0,
        'pass_40_yd_td': 0.0,
        'pick_six': 0.0,
        'rushing_yards_per_point': 10,
        'rushing_tds': 6.0,
        'carries': 0.0,
        'rush_40_yd': 0.0,
        'receptions': 0.0,
        'receiving_yards_per_point': 10,
        'receiving_tds': 6.0,
        'rec_40_yd': 0.0,
        'fumbles_lost': -2.0,
        'two_pt_conversions': 2.0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()


@st.cache_data(show_spinner="Loading NFL data...")
def load_data(year: int):
    """Load and cache all NFL data for a year."""
    stats = load_seasonal_stats(year)
    pbp = load_pbp_data(year)

    # nflreadpy player_stats already includes player_name, position, recent_team
    # Rename recent_team to team for consistency
    stats = stats.rename(columns={'recent_team': 'team'})

    # Filter to skill positions
    skill_positions = ['QB', 'RB', 'WR', 'TE']
    stats = stats[stats['position'].isin(skill_positions)]

    # Aggregate PBP stats
    pbp_stats = aggregate_pbp_stats(pbp)

    return stats, pbp_stats


def get_config_from_sliders() -> ScoringConfig:
    """Build scoring config from sidebar slider values."""
    return ScoringConfig(
        name="Custom",
        # Passing
        passing_yards_per_point=st.session_state.get('passing_yards_per_point', 25),
        passing_tds=st.session_state.get('passing_tds', 4.0),
        interceptions=st.session_state.get('interceptions', -1.0),
        completions=st.session_state.get('completions', 0.0),
        pass_40_yd=st.session_state.get('pass_40_yd', 0.0),
        pass_40_yd_td=st.session_state.get('pass_40_yd_td', 0.0),
        pick_six=st.session_state.get('pick_six', 0.0),
        # Rushing
        rushing_yards_per_point=st.session_state.get('rushing_yards_per_point', 10),
        rushing_tds=st.session_state.get('rushing_tds', 6.0),
        carries=st.session_state.get('carries', 0.0),
        rush_40_yd=st.session_state.get('rush_40_yd', 0.0),
        # Receiving
        receptions=st.session_state.get('receptions', 0.0),
        receiving_yards_per_point=st.session_state.get('receiving_yards_per_point', 10),
        receiving_tds=st.session_state.get('receiving_tds', 6.0),
        rec_40_yd=st.session_state.get('rec_40_yd', 0.0),
        # Misc
        fumbles_lost=st.session_state.get('fumbles_lost', -2.0),
        two_pt_conversions=st.session_state.get('two_pt_conversions', 2.0),
    )


def apply_preset(preset: str):
    """Apply a preset scoring configuration."""
    if preset == "Standard":
        st.session_state['passing_yards_per_point'] = 25
        st.session_state['passing_tds'] = 4.0
        st.session_state['interceptions'] = -1.0
        st.session_state['completions'] = 0.0
        st.session_state['pass_40_yd'] = 0.0
        st.session_state['pass_40_yd_td'] = 0.0
        st.session_state['pick_six'] = 0.0
        st.session_state['rushing_yards_per_point'] = 10
        st.session_state['rushing_tds'] = 6.0
        st.session_state['carries'] = 0.0
        st.session_state['rush_40_yd'] = 0.0
        st.session_state['receptions'] = 0.0
        st.session_state['receiving_yards_per_point'] = 10
        st.session_state['receiving_tds'] = 6.0
        st.session_state['rec_40_yd'] = 0.0
        st.session_state['fumbles_lost'] = -2.0
        st.session_state['two_pt_conversions'] = 2.0
    elif preset == "PPR":
        apply_preset("Standard")
        st.session_state['receptions'] = 1.0
    elif preset == "Half-PPR":
        apply_preset("Standard")
        st.session_state['receptions'] = 0.5


# Sidebar
with st.sidebar:
    st.header("Settings")

    # Year selector
    year = st.selectbox(
        "Season",
        options=list(range(2024, 2019, -1)),
        index=0,
    )

    st.divider()

    # Presets
    st.subheader("Presets")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Standard", use_container_width=True):
            apply_preset("Standard")
            st.rerun()
    with col2:
        if st.button("PPR", use_container_width=True):
            apply_preset("PPR")
            st.rerun()
    with col3:
        if st.button("Half-PPR", use_container_width=True):
            apply_preset("Half-PPR")
            st.rerun()

    st.divider()

    # Passing
    st.subheader("Passing")
    st.slider(
        "Yards per Point",
        min_value=10, max_value=50, step=1,
        key='passing_yards_per_point',
        help="How many passing yards equal 1 point"
    )
    st.slider(
        "Passing TDs",
        min_value=0.0, max_value=8.0, step=0.05,
        key='passing_tds',
        format="%.2f"
    )
    st.slider(
        "Interceptions",
        min_value=-4.0, max_value=0.0, step=0.05,
        key='interceptions',
        format="%.2f"
    )
    st.slider(
        "Completions",
        min_value=0.0, max_value=1.0, step=0.05,
        key='completions',
        format="%.2f"
    )
    st.slider(
        "40+ Yd Completions",
        min_value=0.0, max_value=4.0, step=0.05,
        key='pass_40_yd',
        format="%.2f"
    )
    st.slider(
        "40+ Yd Pass TDs",
        min_value=0.0, max_value=4.0, step=0.05,
        key='pass_40_yd_td',
        format="%.2f"
    )
    st.slider(
        "Pick Sixes",
        min_value=-4.0, max_value=0.0, step=0.05,
        key='pick_six',
        format="%.2f"
    )

    st.divider()

    # Rushing
    st.subheader("Rushing")
    st.slider(
        "Yards per Point",
        min_value=5, max_value=20, step=1,
        key='rushing_yards_per_point',
        help="How many rushing yards equal 1 point"
    )
    st.slider(
        "Rushing TDs",
        min_value=0.0, max_value=10.0, step=0.05,
        key='rushing_tds',
        format="%.2f"
    )
    st.slider(
        "Rushing Attempts",
        min_value=0.0, max_value=1.0, step=0.05,
        key='carries',
        format="%.2f"
    )
    st.slider(
        "40+ Yd Rushes",
        min_value=0.0, max_value=4.0, step=0.05,
        key='rush_40_yd',
        format="%.2f"
    )

    st.divider()

    # Receiving
    st.subheader("Receiving")
    st.slider(
        "Receptions (PPR)",
        min_value=0.0, max_value=2.0, step=0.05,
        key='receptions',
        format="%.2f"
    )
    st.slider(
        "Yards per Point",
        min_value=5, max_value=20, step=1,
        key='receiving_yards_per_point',
        help="How many receiving yards equal 1 point"
    )
    st.slider(
        "Receiving TDs",
        min_value=0.0, max_value=10.0, step=0.05,
        key='receiving_tds',
        format="%.2f"
    )
    st.slider(
        "40+ Yd Receptions",
        min_value=0.0, max_value=4.0, step=0.05,
        key='rec_40_yd',
        format="%.2f"
    )

    st.divider()

    # Misc
    st.subheader("Miscellaneous")
    st.slider(
        "Fumbles Lost",
        min_value=-4.0, max_value=0.0, step=0.05,
        key='fumbles_lost',
        format="%.2f"
    )
    st.slider(
        "2-PT Conversions",
        min_value=0.0, max_value=4.0, step=0.05,
        key='two_pt_conversions',
        format="%.2f"
    )


# Main content
try:
    # Load data
    stats, pbp_stats = load_data(year)

    # Get current config from sliders
    current_config = get_config_from_sliders()

    # Calculate fantasy points with current config
    current_scored = calculate_fantasy_points(stats, pbp_stats, current_config)

    # Calculate baseline (Yahoo Standard) for comparison
    baseline_config = get_yahoo_standard()
    baseline_scored = calculate_fantasy_points(stats, pbp_stats, baseline_config)

    # Get rankings
    position_rankings = rank_by_position(current_scored)

    # Calculate position means for top 12, top 36, and 25-36 range
    position_means_12 = calculate_position_means(current_scored, POSITION_MEAN_LIMIT_12)
    position_means_36 = calculate_position_means(current_scored, POSITION_MEAN_LIMIT_36)
    position_means_25_36 = calculate_position_means_range(current_scored, 25, 36)

    # Display position rankings
    st.header(f"{year} Season Rankings")

    # Show mean points per position - Top 12
    st.subheader(f"Average Points (Top {POSITION_MEAN_LIMIT_12} per position)")
    mean_cols_12 = st.columns(4)
    for i, (pos, mean_pts) in enumerate(position_means_12.items()):
        with mean_cols_12[i]:
            st.metric(label=pos, value=f"{mean_pts:.1f} pts")

    # Show mean points per position - Top 36
    st.subheader(f"Average Points (Top {POSITION_MEAN_LIMIT_36} per position)")
    mean_cols_36 = st.columns(4)
    for i, (pos, mean_pts) in enumerate(position_means_36.items()):
        with mean_cols_36[i]:
            st.metric(label=pos, value=f"{mean_pts:.1f} pts")

    # Show mean points per position - Ranks 25-36
    st.subheader("Average Points (Ranks 25-36 per position)")
    mean_cols_25_36 = st.columns(4)
    for i, (pos, mean_pts) in enumerate(position_means_25_36.items()):
        with mean_cols_25_36[i]:
            st.metric(label=pos, value=f"{mean_pts:.1f} pts")

    st.divider()

    # Create two columns for QB/RB and WR/TE
    col1, col2 = st.columns(2)

    with col1:
        st.subheader(f"Top {POSITION_LIMITS['QB']} QB")
        qb_table = format_position_table(position_rankings['QB'], 'QB')
        st.dataframe(qb_table, use_container_width=True, hide_index=True)

        st.subheader(f"Top {POSITION_LIMITS['RB']} RB")
        rb_table = format_position_table(position_rankings['RB'], 'RB')
        st.dataframe(rb_table, use_container_width=True, hide_index=True)

    with col2:
        st.subheader(f"Top {POSITION_LIMITS['WR']} WR")
        wr_table = format_position_table(position_rankings['WR'], 'WR')
        st.dataframe(wr_table, use_container_width=True, hide_index=True)

        st.subheader(f"Top {POSITION_LIMITS['TE']} TE")
        te_table = format_position_table(position_rankings['TE'], 'TE')
        st.dataframe(te_table, use_container_width=True, hide_index=True)

    # Risers and Fallers
    st.divider()
    st.header("Risers & Fallers vs Yahoo Standard")

    risers, fallers = compare_rankings(current_scored, baseline_scored)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Biggest Risers")
        if not risers.empty:
            risers_table = format_risers_fallers(risers)
            st.dataframe(risers_table, use_container_width=True, hide_index=True)
        else:
            st.info("No significant risers with current settings")

    with col2:
        st.subheader("Biggest Fallers")
        if not fallers.empty:
            fallers_table = format_risers_fallers(fallers)
            st.dataframe(fallers_table, use_container_width=True, hide_index=True)
        else:
            st.info("No significant fallers with current settings")

except Exception as e:
    st.error(f"Error loading data: {e}")
    st.info("Make sure you have an internet connection for the initial data download.")
