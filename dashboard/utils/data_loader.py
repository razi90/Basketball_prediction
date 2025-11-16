"""
Data loading utilities for the dashboard.

Loads prediction data, statistics, and historical results from database.
CSV processing has been removed in favor of database-only approach.
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd

# Add src to path for imports
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.utils.db_utils import DatabaseOperations, db_config


def load_latest_predictions(limit: int = 100) -> Optional[pd.DataFrame]:
    """
    Load the most recent predictions from database.

    Args:
        limit: Maximum number of predictions to load

    Returns:
        DataFrame with predictions or None if not found
    """
    if not db_config.enabled:
        return None

    try:
        db_ops = DatabaseOperations()
        df = db_ops.get_latest_predictions(limit=limit)
        return df if not df.empty else None
    except Exception as e:
        print(f"Error loading predictions: {e}")
        return None


def load_enriched_predictions(limit: int = 100) -> Optional[pd.DataFrame]:
    """
    Load the most recent enriched predictions with betting suggestions from database.

    Args:
        limit: Maximum number of predictions to load

    Returns:
        DataFrame with enriched predictions or None if not found
    """
    if not db_config.enabled:
        return None

    try:
        db_ops = DatabaseOperations()
        # Try to get enriched predictions if available
        df = db_ops.get_latest_predictions(limit=limit)
        return df if not df.empty else None
    except Exception as e:
        print(f"Error loading enriched predictions: {e}")
        return None


def load_betting_statistics() -> Optional[pd.DataFrame]:
    """
    Load betting statistics and accuracy metrics from database.

    Returns:
        DataFrame with betting stats or None if not found
    """
    if not db_config.enabled:
        return None

    try:
        db_ops = DatabaseOperations()
        # Get betting performance metrics
        metrics = db_ops.get_betting_performance()
        if metrics:
            return pd.DataFrame([metrics])
        return None
    except Exception as e:
        print(f"Error loading betting statistics: {e}")
        return None


def load_historical_games(days_back: int = 30) -> Optional[pd.DataFrame]:
    """
    Load historical game data from the past N days from database.

    Args:
        days_back: Number of days of history to load

    Returns:
        DataFrame with historical games or None if not found
    """
    if not db_config.enabled:
        return None

    try:
        db_ops = DatabaseOperations()
        df = db_ops.get_latest_game_statistics(limit=None)

        if df.empty:
            return None

        # Filter to past N days
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            cutoff_date = datetime.now() - timedelta(days=days_back)
            df = df[df["date"] >= cutoff_date]

        return df if not df.empty else None
    except Exception as e:
        print(f"Error loading historical games: {e}")
        return None


def load_all_predictions(limit: int = 100) -> Optional[pd.DataFrame]:
    """
    Load multiple predictions for historical analysis from database.

    Args:
        limit: Maximum number of predictions to load

    Returns:
        DataFrame with all predictions or None if not found
    """
    if not db_config.enabled:
        return None

    try:
        db_ops = DatabaseOperations()
        df = db_ops.get_latest_predictions(limit=limit)
        return df if not df.empty else None
    except Exception as e:
        print(f"Error loading all predictions: {e}")
        return None


def get_team_stats(team: str, df: pd.DataFrame) -> dict:
    """
    Calculate statistics for a specific team.

    Args:
        team: Team abbreviation (e.g., "LAL")
        df: DataFrame with game data

    Returns:
        Dictionary with team statistics
    """
    team_games = df[df["team"] == team]

    if len(team_games) == 0:
        return {}

    stats = {
        "games_played": len(team_games),
        "wins": team_games["won"].sum() if "won" in team_games.columns else 0,
        "losses": len(team_games) - (team_games["won"].sum() if "won" in team_games.columns else 0),
        "avg_points": team_games["pts"].mean() if "pts" in team_games.columns else 0,
        "avg_opp_points": team_games["opp_pts"].mean() if "opp_pts" in team_games.columns else 0,
    }

    if "won" in team_games.columns and stats["games_played"] > 0:
        stats["win_pct"] = stats["wins"] / stats["games_played"]
    else:
        stats["win_pct"] = 0.0

    return stats


def calculate_model_metrics(df: pd.DataFrame) -> dict:
    """
    Calculate model performance metrics.

    Args:
        df: DataFrame with predictions and actual results

    Returns:
        Dictionary with performance metrics
    """
    metrics = {}

    if "won" in df.columns and "predicted_prob" in df.columns:
        # Accuracy
        df["predicted"] = (df["predicted_prob"] > 0.5).astype(int)
        metrics["accuracy"] = (df["predicted"] == df["won"]).mean()

        # Brier score (lower is better)
        metrics["brier_score"] = ((df["predicted_prob"] - df["won"]) ** 2).mean()

        # Log loss
        import numpy as np

        epsilon = 1e-15
        probs = df["predicted_prob"].clip(epsilon, 1 - epsilon)
        metrics["log_loss"] = -(
            df["won"] * np.log(probs) + (1 - df["won"]) * np.log(1 - probs)
        ).mean()

    if "recommended_stake" in df.columns:
        # Calculate ROI
        df_with_stakes = df[df["recommended_stake"] > 0].copy()
        if len(df_with_stakes) > 0:
            # Simplified ROI calculation (would need actual bet outcomes)
            metrics["total_bets"] = len(df_with_stakes)
            metrics["avg_stake"] = df_with_stakes["recommended_stake"].mean()

    return metrics


def get_available_data_summary() -> dict:
    """
    Get summary of available data from database.

    Returns:
        Dictionary with data counts and date ranges
    """
    summary = {
        "database_enabled": db_config.enabled,
        "prediction_count": 0,
        "game_statistics_count": 0,
    }

    if not db_config.enabled:
        return summary

    try:
        db_ops = DatabaseOperations()

        # Get prediction count
        predictions = db_ops.get_latest_predictions(limit=1000)
        summary["prediction_count"] = len(predictions)

        if not predictions.empty and "date" in predictions.columns:
            predictions["date"] = pd.to_datetime(predictions["date"])
            summary["earliest_prediction"] = predictions["date"].min().strftime("%Y-%m-%d")
            summary["latest_prediction"] = predictions["date"].max().strftime("%Y-%m-%d")

        # Get game statistics count
        games = db_ops.get_latest_game_statistics(limit=1000)
        summary["game_statistics_count"] = len(games)

        if not games.empty and "date" in games.columns:
            games["date"] = pd.to_datetime(games["date"])
            summary["earliest_game"] = games["date"].min().strftime("%Y-%m-%d")
            summary["latest_game"] = games["date"].max().strftime("%Y-%m-%d")

    except Exception as e:
        print(f"Error getting data summary: {e}")

    return summary
