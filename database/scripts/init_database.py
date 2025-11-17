#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Initialize Database with CSV Data

This script automatically populates the database from CSV files if the database is empty.
Designed to run automatically in Docker Compose on first startup.

Usage:
    python init_database.py [--csv-dir /path/to/csvs] [--force]

Options:
    --csv-dir       Directory containing CSV files (default: auto-detect)
    --force         Force migration even if data already exists
    --dry-run       Show what would be migrated without actually doing it
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.db_utils import DatabaseOperations, db_pool
from src.utils.logger import get_logger
from src.utils.nba_utils import get_directory_paths

logger = get_logger(__name__)


def check_database_empty() -> bool:
    """Check if the database has any data.

    Returns:
        True if database is empty, False otherwise
    """
    try:
        db_ops = DatabaseOperations()

        # Check if game_statistics table has data
        stats = db_ops.get_latest_game_statistics(limit=1)
        if not stats.empty:
            logger.info("Database already has game statistics data")
            return False

        logger.info("Database is empty - will populate from CSV files")
        return True

    except Exception as e:
        logger.error(f"Error checking database: {e}")
        # If there's an error, assume empty and try to populate
        return True


def run_migration_script(script_name: str, csv_dir: Optional[str] = None, dry_run: bool = False) -> bool:
    """Run a migration script.

    Args:
        script_name: Name of migration script (e.g., 'migrate_game_statistics.py')
        csv_dir: Optional CSV directory path
        dry_run: If True, don't actually insert data

    Returns:
        True if successful, False otherwise
    """
    import subprocess

    script_dir = Path(__file__).parent
    script_path = script_dir / script_name

    if not script_path.exists():
        logger.error(f"Migration script not found: {script_path}")
        return False

    logger.info(f"Running migration script: {script_name}")

    # Build command
    cmd = [sys.executable, str(script_path)]

    if dry_run:
        cmd.append("--dry-run")

    # Run the script
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=script_dir.parent.parent,  # Run from project root
        )

        # Log output
        if result.stdout:
            logger.info(f"Script output:\n{result.stdout}")
        if result.stderr:
            logger.warning(f"Script warnings:\n{result.stderr}")

        if result.returncode == 0:
            logger.info(f"✅ {script_name} completed successfully")
            return True
        else:
            logger.error(f"❌ {script_name} failed with code {result.returncode}")
            return False

    except Exception as e:
        logger.error(f"Error running {script_name}: {e}")
        return False


def initialize_database(csv_dir: Optional[str] = None, force: bool = False, dry_run: bool = False) -> bool:
    """Initialize database with CSV data if needed.

    Args:
        csv_dir: Directory containing CSV files
        force: Force migration even if data exists
        dry_run: Show what would be done without doing it

    Returns:
        True if successful, False otherwise
    """
    logger.info("=" * 60)
    logger.info("DATABASE INITIALIZATION")
    logger.info("=" * 60)

    try:
        # Initialize database connection pool
        logger.info("Initializing database connection pool...")
        db_pool.initialize()
        logger.info("✅ Database connection established")

        # Check if database needs initialization
        if not force and not check_database_empty():
            logger.info("Database already populated. Use --force to re-populate.")
            return True

        # Run migration scripts in order
        migrations = [
            "migrate_game_statistics.py",
            "migrate_predictions.py",
            "migrate_enriched_predictions.py",
        ]

        logger.info(f"\n📦 Running {len(migrations)} migration scripts...")

        success_count = 0
        for migration in migrations:
            logger.info(f"\n--- Migration: {migration} ---")
            if run_migration_script(migration, csv_dir, dry_run):
                success_count += 1
            else:
                logger.warning(f"⚠️  {migration} had issues, continuing anyway...")

        logger.info("\n" + "=" * 60)
        logger.info(f"INITIALIZATION COMPLETE: {success_count}/{len(migrations)} migrations successful")
        logger.info("=" * 60)

        return success_count > 0

    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        return False
    finally:
        # Close database connections
        try:
            db_pool.close_all()
        except:
            pass


def main():
    parser = argparse.ArgumentParser(description="Initialize database from CSV files")
    parser.add_argument("--csv-dir", help="Directory containing CSV files")
    parser.add_argument("--force", action="store_true", help="Force migration even if data exists")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")

    args = parser.parse_args()

    # Run initialization
    success = initialize_database(
        csv_dir=args.csv_dir,
        force=args.force,
        dry_run=args.dry_run
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
