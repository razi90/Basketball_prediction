# Quick Start Guide - Database-Only Basketball Prediction

## 🚀 Get Started in 3 Steps

### 1. Prepare Your CSV Files

Place your CSV files in the correct directories:

```bash
Basketball_prediction/
└── output/
    └── Gathering_Data/
        ├── Whole_Statistic/
        │   └── nba_games_2024-11-15.csv    # Historical game statistics
        ├── Next_Game/
        │   └── games_df_2024-11-15.csv     # Upcoming games schedule
        └── LightGBM/
            ├── predictions_2024-11-15.csv         # (Optional)
            └── enriched_predictions_2024-11-15.csv # (Optional)
```

### 2. Start Docker Compose

```bash
cd Basketball_prediction

# First time - will automatically populate database from CSV files
docker-compose up -d

# Watch the initialization process
docker-compose logs -f app
```

You'll see:
```
⏳ Waiting for database to be ready...
✅ Database is ready!
🔍 Checking if database needs initialization...
📦 Running 3 migration scripts...
--- Migration: migrate_game_statistics.py ---
✅ migrate_game_statistics.py completed successfully
...
🚀 Starting application...
```

### 3. Use the Application

```bash
# Access the dashboard
open http://localhost:8501

# Or run predictions manually
docker-compose exec app nba-predict predict

# Or run analysis
docker-compose exec app nba-predict analyze kelly
```

## 📋 Environment Setup

Create a `.env` file:

```bash
# Database (automatically configured in docker-compose)
POSTGRES_PASSWORD=changeme123

# Optional: Odds API
ODDS_API_KEY=your_api_key_here

# Optional: Skip auto-initialization (after first run)
SKIP_DB_INIT=false
```

## 🔄 Common Operations

### Run Predictions

```bash
# Inside Docker
docker-compose exec app nba-predict predict

# Or locally (if installed)
nba-predict predict
```

### Analyze Betting Performance

```bash
docker-compose exec app nba-predict analyze statistics
docker-compose exec app nba-predict analyze kelly
```

### Check Database Status

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U nba_user -d nba_predictions

# Check data counts
docker-compose exec postgres psql -U nba_user -d nba_predictions -c "
  SELECT 'game_statistics' as table, COUNT(*) as rows FROM game_statistics
  UNION ALL
  SELECT 'predictions', COUNT(*) FROM predictions;
"
```

### Force Re-initialization

```bash
# Option 1: Delete volume and restart (fresh start)
docker-compose down -v
docker-compose up -d

# Option 2: Force re-populate existing database
docker-compose exec app python database/scripts/init_database.py --force
```

## 🛠️ Development Mode

```bash
# Run with local code changes
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Run CLI commands
docker-compose exec app bash
python -m src.cli.main predict
```

## 📊 Data Flow

```
CSV Files (output/Gathering_Data/)
    ↓
Docker Entrypoint (docker/entrypoint.sh)
    ↓
Init Database Script (database/scripts/init_database.py)
    ↓
Migration Scripts (migrate_*.py)
    ↓
PostgreSQL Database
    ↓
Application (predictor, analyzer, dashboard)
```

## ❓ Troubleshooting

### Database won't start
```bash
# Check logs
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up -d
```

### CSV files not loading
```bash
# Check file permissions
chmod -R 755 output/

# Check if files exist
ls -la output/Gathering_Data/Whole_Statistic/

# Run migration manually
docker-compose exec app python database/scripts/migrate_game_statistics.py
```

### Application errors
```bash
# Check application logs
docker-compose logs app

# Check database connection
docker-compose exec app python -c "
from src.utils.db_utils import db_pool
db_pool.initialize()
print('✅ Database connection successful')
"
```

## 📚 Next Steps

- [Full Database Documentation](README-DATABASE.md)
- [API Reference](docs/API.md)
- [Contributing Guidelines](CONTRIBUTING.md)

## 🎯 Key Changes from CSV-Only Approach

| Before (CSV) | Now (Database) |
|--------------|----------------|
| Files scattered in multiple directories | Single source of truth in PostgreSQL |
| Manual file management | Automatic initialization |
| `USE_DATABASE=true` required | Database always used |
| CSV read/write in code | Database operations only |
| Complex file searching logic | Simple database queries |

## 💡 Pro Tips

1. **First Run**: Let Docker Compose populate the database automatically
2. **After Initial Setup**: Set `SKIP_DB_INIT=true` to skip initialization check
3. **Backups**: Schedule regular database backups (see README-DATABASE.md)
4. **Development**: Use `docker-compose exec app bash` for interactive debugging
5. **Production**: Use environment-specific compose files and secrets management

## 🆘 Support

- [Open an Issue](https://github.com/razi90/Basketball_prediction/issues)
- [Check Logs](docker-compose logs -f)
- [Database Guide](README-DATABASE.md)
