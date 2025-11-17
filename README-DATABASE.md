# Database Initialization with Docker Compose

This guide explains how to automatically populate the database from CSV files using Docker Compose.

## Quick Start

### First Time Setup

1. **Place your CSV files** in the appropriate directory:
   ```bash
   # Game statistics
   ./output/Gathering_Data/Whole_Statistic/nba_games_*.csv

   # Upcoming games
   ./output/Gathering_Data/Next_Game/games_df_*.csv

   # Predictions (optional)
   ./output/LightGBM/predictions_*.csv
   ./output/LightGBM/enriched_predictions_*.csv
   ```

2. **Start the services**:
   ```bash
   docker-compose up -d
   ```

3. **Watch the initialization**:
   ```bash
   docker-compose logs -f app
   ```

The database will **automatically initialize** with data from CSV files on first startup!

## How It Works

### Automatic Database Population

When you start the containers:

1. **PostgreSQL starts** and creates the database schema
2. **App container waits** for database to be ready
3. **Initialization script runs** (`database/scripts/init_database.py`)
   - Checks if database is empty
   - If empty, runs migration scripts to load CSV data
   - Migrates game statistics, predictions, and enriched predictions
4. **Application starts** with populated database

### Environment Variables

Configure behavior with environment variables in `.env` or `docker-compose.yml`:

```bash
# Database connection
DB_HOST=postgres
DB_PORT=5432
DB_NAME=nba_predictions
DB_USER=nba_user
DB_PASSWORD=changeme123

# Skip auto-initialization (if data already exists)
SKIP_DB_INIT=false  # Set to 'true' to skip
```

## Manual Operations

### Force Re-initialization

If you want to re-populate the database:

```bash
# Option 1: Via environment variable
SKIP_DB_INIT=false docker-compose up -d app

# Option 2: Run init script manually
docker-compose exec app python /app/database/scripts/init_database.py --force

# Option 3: Delete database volume and restart
docker-compose down -v
docker-compose up -d
```

### Run Individual Migration Scripts

```bash
# Migrate game statistics only
docker-compose exec app python database/scripts/migrate_game_statistics.py

# Migrate predictions only
docker-compose exec app python database/scripts/migrate_predictions.py

# Migrate enriched predictions only
docker-compose exec app python database/scripts/migrate_enriched_predictions.py

# Dry run (see what would be migrated)
docker-compose exec app python database/scripts/init_database.py --dry-run
```

### Check Database Status

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U nba_user -d nba_predictions

# Check row counts
docker-compose exec postgres psql -U nba_user -d nba_predictions -c "
  SELECT
    'game_statistics' as table_name,
    COUNT(*) as rows
  FROM game_statistics
  UNION ALL
  SELECT
    'predictions',
    COUNT(*)
  FROM predictions
  UNION ALL
  SELECT
    'enriched_predictions',
    COUNT(*)
  FROM enriched_predictions;
"
```

## Directory Structure

```
Basketball_prediction/
├── output/
│   └── Gathering_Data/
│       ├── Whole_Statistic/      # Game statistics CSVs
│       │   └── nba_games_*.csv
│       ├── Next_Game/             # Upcoming games CSVs
│       │   └── games_df_*.csv
│       └── LightGBM/              # Prediction CSVs (optional)
│           ├── predictions_*.csv
│           └── enriched_predictions_*.csv
│
├── database/
│   ├── schemas/
│   │   └── schema.sql             # Database schema
│   └── scripts/
│       ├── init_database.py       # Auto-initialization script
│       ├── migrate_game_statistics.py
│       ├── migrate_predictions.py
│       └── migrate_enriched_predictions.py
│
├── docker/
│   └── entrypoint.sh              # Container entrypoint
│
├── docker-compose.yml
└── Dockerfile
```

## Troubleshooting

### Database Won't Initialize

Check logs:
```bash
docker-compose logs app
```

Common issues:
- CSV files not in correct directory
- Permissions issues (use `chmod -R 755 output/`)
- Database connection failed (check `DB_*` environment variables)

### Data Already Exists

If you see "Database already has data":
```bash
# Option 1: Force re-initialization
docker-compose exec app python database/scripts/init_database.py --force

# Option 2: Clear database and restart
docker-compose down -v  # WARNING: Deletes all data
docker-compose up -d
```

### Performance Tuning

For large CSV files, adjust batch size:
```bash
docker-compose exec app python database/scripts/migrate_game_statistics.py --batch-size 5000
```

## Production Deployment

For production:

1. **Set strong passwords** in `.env`:
   ```bash
   POSTGRES_PASSWORD=<strong-random-password>
   ```

2. **Run initialization once**, then skip:
   ```bash
   SKIP_DB_INIT=true
   ```

3. **Backup database** regularly:
   ```bash
   docker-compose exec postgres pg_dump -U nba_user nba_predictions > backup.sql
   ```

4. **Use secrets management** (Docker Secrets, Kubernetes Secrets, etc.)

## Advanced Usage

### Custom CSV Directory

Mount a different CSV directory:
```yaml
volumes:
  - /path/to/my/csvs:/app/output/Gathering_Data:ro
```

### Multiple Environments

Use different compose files:
```bash
# Development
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up
```

### Database Backup Schedule

Add to `docker-compose.yml`:
```yaml
  backup:
    image: postgres:15-alpine
    depends_on:
      - postgres
    volumes:
      - ./backups:/backups
    environment:
      PGPASSWORD: ${POSTGRES_PASSWORD}
    entrypoint: |
      sh -c 'while true; do
        pg_dump -h postgres -U nba_user nba_predictions > /backups/backup_$$(date +%Y%m%d_%H%M%S).sql
        sleep 86400  # Daily backups
      done'
```

## Next Steps

- [Database Schema Documentation](database/schemas/README.md)
- [Migration Scripts Reference](database/scripts/README.md)
- [API Documentation](docs/API.md)
