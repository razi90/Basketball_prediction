#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script 4 of 5: Calculate Betting Statistics

This script merges actual outcomes with predicted results to evaluate betting performance.
It calculates overall and subset accuracies (e.g., home-favored vs. away-favored),
and updates a combined CSV with the results.

Ensure "3_lightgbm_prediction.py" is executed before running this script.
"""

import pandas as pd
import os
import numpy as np
import logging
from datetime import timedelta

# Import shared utilities
from nba_utils import (
    CURRENT_SEASON,
    get_current_date,
    get_directory_paths,
    find_file_in_date_range
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Maximum days to look back for files
MAX_DAYS_BACK = 120  # Configurable range for searching files

# Get current date information
today, today_str, today_str_format = get_current_date()
yesterday, yesterday_str, yesterday_str_format = get_current_date(days_offset=1)

print(f"Today's date: {today_str_format}")
print(f"Looking for data from: {yesterday_str_format}")
print(yesterday)

# Get directory paths
paths = get_directory_paths()
BASE_DIR = paths['BASE_DIR']
DATA_DIR = paths['DATA_DIR']
STAT_DIR = paths['STAT_DIR']
target_folder = paths['NEXT_GAME_DIR']
directory_path = paths['PREDICTION_DIR']

def find_most_recent_prediction_file():
    """Find the most recent prediction file within the specified days range."""
    days_back = 0
    file_found = False

    while not file_found and days_back <= MAX_DAYS_BACK:
        # Recalculate the date string on every loop iteration
        date_to_check = yesterday - timedelta(days=days_back)
        date_str = date_to_check.strftime("%Y-%m-%d")

        print(f"Checking date: {date_str}")

        filename = f"nba_games_predict_{date_str}.csv"
        file_path = os.path.join(directory_path, filename)

        if os.path.isfile(file_path):
            file_found = True
            print(f"The file for {date_str} exists.")
            predict_file = [file_path]
            last_prediction = date_str
            return predict_file, last_prediction
        else:
            days_back += 1

    print("No file found in the last 120 days.")
    return None, None

def find_most_recent_statistics_file():
    """Find the most recent statistics file within the specified days range."""
    file_path, date_str = find_file_in_date_range(
        STAT_DIR,
        f"nba_games_{{}}.csv",
        MAX_DAYS_BACK
    )

    if file_path:
        logging.info(f"The file for {date_str} exists.")
        return date_str
    else:
        logging.warning("No statistics file found within the specified range.")
        return None

def process_prediction_file(predict_file, last_prediction):
    """
    Process the prediction file and update the combined predictions.

    Args:
        predict_file (list): List containing the path to the prediction file
        last_prediction (str): Date string of the last prediction

    Returns:
        DataFrame: Combined predictions DataFrame or None if no file found
    """
    if not predict_file:
        print(f"No prediction file found.")
        return None

    # Read prediction file
    predict_file_df = pd.read_csv(predict_file[0], encoding="utf-7", decimal=",")

    # Columns to display
    columns_to_display = ['home_team', 'away_team', 'home_team_prob', 'odds 1', 'odds 2', 'result', 'date']

    # Convert 'odds 1' and 'odds 2' from comma as decimal separator to period
    predict_file_df['odds 1'] = predict_file_df['odds 1'].astype(str).str.replace(',', '.').astype(float)
    predict_file_df['odds 2'] = predict_file_df['odds 2'].astype(str).str.replace(',', '.').astype(float)

    # File path for combined data
    combined_file_path = os.path.join(directory_path, f'combined_nba_predictions_acc_{last_prediction}.csv')

    try:
        # Attempt to read the combined file
        combined_df = pd.read_csv(combined_file_path, encoding="utf-7", decimal=",")
    except FileNotFoundError:
        # If not found, initialize an empty DataFrame
        combined_df = pd.DataFrame()

    # Append new data to the combined DataFrame
    predict_file_df['accuracy'] = np.nan  # Add 'accuracy' column with NaN
    combined_df = pd.concat([combined_df, predict_file_df], ignore_index=True)

    # Sort the DataFrame by date
    combined_df = combined_df.sort_values(by='date', ascending=False)

    # Select only the desired columns
    combined_df = combined_df[columns_to_display]
    print(combined_df.head(10))

    print(f"Combined predictions updated")
    return combined_df

def update_betting_statistics(combined_df, most_recent_date):
    """
    Update betting statistics with actual game results.

    Args:
        combined_df (DataFrame): DataFrame with combined predictions
        most_recent_date (str): Date string of the most recent statistics file

    Returns:
        DataFrame: Updated statistics DataFrame or None if update failed
    """
    # Make a copy of the combined DataFrame
    season_2025_df = combined_df.copy()

    print(most_recent_date)

    # Read the most recent games data
    daily_games_df = pd.read_csv(os.path.join(STAT_DIR, f"nba_games_{most_recent_date}.csv"))

    # Filter data for the current season
    daily_games_df = daily_games_df[daily_games_df['season'] == CURRENT_SEASON].copy()

    # Convert dates to datetime
    season_2025_df['date'] = pd.to_datetime(season_2025_df['date'], errors='coerce')
    daily_games_df['date'] = pd.to_datetime(daily_games_df['date'], errors='coerce')

    # Iterate over each row in the daily game data and update the result column
    for _, row in daily_games_df.iterrows():
        date = row['date']
        winning_team = row['team'] if row['won'] == 1 else None

        # Update the 'result' column for the corresponding date and teams
        if winning_team:
            mask = (season_2025_df['date'] == date) & (
                (season_2025_df['home_team'] == winning_team) | (season_2025_df['away_team'] == winning_team)
            )

            season_2025_df.loc[mask, 'result'] = winning_team

    # Ensure that 'home_team_prob' is numeric
    season_2025_df['home_team_prob'] = pd.to_numeric(season_2025_df['home_team_prob'], errors='coerce')

    # Check for any invalid values after conversion
    if season_2025_df['home_team_prob'].isnull().any():
        print("Warning: Some values in 'home_team_prob' could not be converted to numeric and have been set to NaN.")

    # Ensure 'result', 'home_team', and 'away_team' columns are strings for comparison
    season_2025_df['result'] = season_2025_df['result'].astype(str)
    season_2025_df['home_team'] = season_2025_df['home_team'].astype(str)
    season_2025_df['away_team'] = season_2025_df['away_team'].astype(str)

    # Create conditions for correct predictions
    home_team_correct = (season_2025_df['home_team_prob'] >= 0.5) & (season_2025_df['result'] == season_2025_df['home_team'])
    away_team_correct = (season_2025_df['home_team_prob'] < 0.5) & (season_2025_df['result'] == season_2025_df['away_team'])

    # Calculate accuracy for each row
    season_2025_df['accuracy'] = (home_team_correct | away_team_correct).astype(int)

    # Overall Accuracy
    overall_accuracy = season_2025_df['accuracy'].mean()
    print(f'Overall Accuracy: {overall_accuracy:.2%}')

    # Filter the DataFrame for specific subsets
    subset_df = season_2025_df[(season_2025_df['home_team_prob'] <= 0.400)]
    subset_df_home = season_2025_df[(season_2025_df['home_team_prob'] > 0.6)]

    # Calculate accuracy for the subsets
    subset_accuracy = subset_df['accuracy'].mean()
    subset_accuracy_home = subset_df_home['accuracy'].mean()

    print(f'Accuracy for home_team_prob above 0.60: {subset_accuracy_home:.2%}')
    print(f'Accuracy for home_team_prob under 0.40 (away team wins): {subset_accuracy:.2%}')

    # Save the updated DataFrame
    save_file_path = os.path.join(directory_path, f'combined_nba_predictions_acc_{today_str_format}.csv')
    print(save_file_path)

    # Drop unnecessary columns if they exist
    season_2025_df.drop(columns=['Unnamed: 8'], errors='ignore', inplace=True)
    season_2025_df.dropna(inplace=True)

    # Save the final DataFrame
    season_2025_df.to_csv(save_file_path, index=False)

    return season_2025_df

def main():
    """Main execution function."""
    # Find the most recent prediction file
    predict_file, last_prediction = find_most_recent_prediction_file()

    if predict_file:
        # Process the prediction file
        combined_df = process_prediction_file(predict_file, last_prediction)

        if combined_df is not None:
            # Find the most recent statistics file
            most_recent_date = find_most_recent_statistics_file()

            if most_recent_date:
                # Update betting statistics
                updated_df = update_betting_statistics(combined_df, most_recent_date)

                if updated_df is not None:
                    print("Betting statistics updated successfully.")
                else:
                    print("Failed to update betting statistics.")
            else:
                print("No recent statistics file found.")
        else:
            print("Failed to process prediction file.")
    else:
        print("No recent prediction file found.")

if __name__ == "__main__":
    main()