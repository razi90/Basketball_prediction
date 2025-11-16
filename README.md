# Basketball Prediction System

[![Tests](https://github.com/razi90/Basketball_prediction/actions/workflows/tests.yml/badge.svg)](https://github.com/razi90/Basketball_prediction/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/razi90/Basketball_prediction/branch/main/graph/badge.svg)](https://codecov.io/gh/razi90/Basketball_prediction)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**End-to-End NBA Betting Prediction & Analytics Platform (2025-26 Season)**

Automates **NBA data scraping, machine learning predictions, and betting analytics** with production-grade infrastructure:
- **Web Scraping**: Selenium + BeautifulSoup for real-time game data
- **Machine Learning**: LightGBM with probability calibration (Platt + Isotonic)
- **Betting Strategy**: Kelly Criterion optimal stake sizing
- **Error Handling**: Comprehensive logging, retries, and graceful fallbacks
- **Storage**: Dual-mode (CSV + optional PostgreSQL/Supabase)
- **Testing**: Comprehensive test coverage with pytest
- **CI/CD**: Automated testing & quality checks via GitHub Actions

---

## Execution Workflow

The system operates through a modular CLI-based pipeline with the following components:

### 1. Data Collection (`src/core/collector.py`)
**Commands**: `nba-predict collect historical`, `nba-predict collect upcoming`
- **Purpose**: Scrapes NBA game data using Selenium + BeautifulSoup
- **Classes**:
  - `HistoricalGameCollector`: Scrapes completed games from Basketball-Reference.com
  - `UpcomingGameCollector`: Fetches upcoming game schedules
- **Output**:
  - CSV: `nba_games_<date>.csv` (155+ game statistics columns)
  - CSV: `games_df_<date>.csv` (upcoming matchups)
  - Database: Automatic save to PostgreSQL/Supabase (if enabled)
- **Features**: Retry logic, error handling, data validation, team normalization

### 2. Prediction Engine (`src/core/predictor.py`)
**Command**: `nba-predict predict`
- **Purpose**: Generates win probability predictions using LightGBM
- **Classes**:
  - `GameDataPreprocessor`: Preprocesses and adds target variables
  - `MatchupBuilder`: Creates home vs away feature matchups
  - `LightGBMPredictor`: Trains model and generates predictions
- **Output**:
  - CSV: `nba_games_predict_<date>.csv` (predictions + odds)
  - Database: Predictions with model tracking (if enabled)
- **Features**:
  - Rolling 9-game averages
  - Live odds integration (The Odds API via `OddsManager`)
  - 300+ engineered features
  - MinMax scaling [0,1]

### 3. Performance Analysis (`src/core/analyzer.py`)
**Commands**: `nba-predict analyze stats`, `nba-predict analyze kelly`
- **Purpose**: Evaluates predictions and calculates betting metrics
- **Classes**:
  - `BettingPerformanceAnalyzer`: Tracks prediction accuracy and performance
  - `HomeWinRateCalculator`: Calculates team-specific win rates
- **Output**: CSV: `combined_nba_predictions_acc_<date>.csv`
- **Features**: Accuracy by team, home/away splits, confidence level analysis

### 4. Betting Strategy (`src/core/betting.py`)
**Commands**: `nba-predict analyze kelly`, `nba-predict analyze recommend`
- **Purpose**: Calculates optimal bet sizes using Kelly Criterion
- **Classes**:
  - `OddsManager`: Fetches live odds from multiple sportsbooks
  - `ProbabilityCalibrator`: Platt + Isotonic calibration
  - `KellyCriterionCalculator`: Optimal stake sizing
  - `BankrollSimulator`: Backtesting and simulation
  - `BetRecommendationDisplay`: Formatted bet display
- **Output**:
  - CSV: `combined_nba_predictions_enriched_<date>.csv`
  - CSV: `home_win_rates_sorted_<date>.csv`
  - Visualization: Bankroll simulation charts
  - Database: Enriched predictions with stakes and P&L (if enabled)
- **Features**:
  - Half-Kelly conservative sizing (50% fraction)
  - Stake caps (30% max, €300 absolute)
  - Three calibration strategies (Raw, Platt, Isotonic)
  - Multi-sportsbook odds (DraftKings, FanDuel, etc.)

### 5. Complete Pipeline
**Command**: `nba-predict pipeline`
- **Purpose**: Runs entire workflow end-to-end
- **Steps**: Collection → Prediction → Analysis → Recommendations
- **Options**: `--skip-collection`, `--skip-analysis` for partial runs

---

## Quick Start

### Prerequisites

- Python 3.12
- Google Chrome (for Selenium web scraping)
- The Odds API key (free tier: https://the-odds-api.com/)
- Optional: Supabase account (for database storage)

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd Basketball_prediction
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env and add your ODDS_API_KEY
```

4. **Install the CLI** (makes `nba-predict` command available)
```bash
pip install -e .
```

5. **Optional: Set up database** (see [DATABASE_SETUP.md](docs/DATABASE_SETUP.md))
```bash
# In .env, add:
USE_DATABASE=true
DATABASE_URL=postgresql://postgres:[password]@db.yourproject.supabase.co:5432/postgres
```

### ⚡ Using the CLI (Recommended)

The modern CLI provides a clean interface to all functionality:

**Run the complete pipeline:**
```bash
nba-predict pipeline
```

**Or run individual steps:**
```bash
# Collect data
nba-predict collect historical
nba-predict collect upcoming

# Generate predictions
nba-predict predict

# Run analysis
nba-predict analyze stats
nba-predict analyze kelly
nba-predict analyze recommend

# Or run all analysis at once
nba-predict analyze all

# Launch dashboard
nba-predict dashboard
```

**Advanced usage:**
```bash
# Skip data collection (use existing data)
nba-predict pipeline --skip-collection

# Skip analysis (only predict)
nba-predict pipeline --skip-analysis

# Collect specific date
nba-predict collect historical --date 2025-11-15

# Get help
nba-predict --help
nba-predict collect --help
```

### 🐳 Docker Setup (Alternative)

![Docker](https://img.shields.io/badge/Docker-20.10+-2496ED.svg?logo=docker)

**Run everything in containers with one command:**

```bash
# Quick start - Dashboard only
docker-compose up dashboard

# Full stack - Dashboard + Database
docker-compose up -d

# Run prediction scripts
docker-compose run --rm app nba-predict predict
```

**Benefits:**
- ✅ **No dependency conflicts** - Isolated environment
- ✅ **Works everywhere** - Linux, Mac, Windows
- ✅ **Includes Chrome/Selenium** - Pre-configured for web scraping
- ✅ **Database included** - Optional PostgreSQL container
- ✅ **One-command setup** - No manual installs

See **[DOCKER.md](DOCKER.md)** for complete Docker setup guide.

### Alternative: Using Python Modules Directly

You can also import and use the modules directly in Python:

```python
from src.core.collector import HistoricalGameCollector, UpcomingGameCollector
from src.core.predictor import LightGBMPredictor
from src.core.analyzer import BettingPerformanceAnalyzer
from src.core.betting import KellyCriterionCalculator
from src.utils.nba_utils import get_current_date

# Collect data
date = get_current_date()
collector = HistoricalGameCollector(date)
collector.collect_games_for_date()

# Make predictions
predictor = LightGBMPredictor()
predictions = predictor.predict_games(date)

# Analyze performance
analyzer = BettingPerformanceAnalyzer()
stats = analyzer.analyze(date)

# Calculate Kelly stakes
kelly = KellyCriterionCalculator()
recommendations = kelly.calculate(date)
```

**Note:** The CLI interface (`nba-predict`) is recommended for better UX, error handling, and logging.

---

## Key Features

### 🗄️ Dual-Mode Storage

The system supports **both CSV and database storage** simultaneously:

**CSV Mode** (Default):
- Works out of the box with no setup
- Portable, version-controllable
- Perfect for development

**Database Mode** (Optional):
- Production-grade PostgreSQL/Supabase
- Advanced querying and analytics
- Automatic audit trails
- Foreign key constraints
- Concurrent access support

Enable database: `USE_DATABASE=true` in `.env`

See **[DATABASE_SETUP.md](docs/DATABASE_SETUP.md)** for complete setup guide.

### 📊 Interactive Dashboard

![Streamlit](https://img.shields.io/badge/Streamlit-1.28.1-FF4B4B.svg)
![Plotly](https://img.shields.io/badge/Plotly-5.17.0-3F4F75.svg)

Launch the **interactive web dashboard** to visualize predictions and analytics:

```bash
streamlit run dashboard/app.py
```

**Dashboard Features**:
- **📊 Today's Games**: Live predictions with win probabilities and betting recommendations
- **📈 Performance Analytics**: Model accuracy, calibration plots, ROI trends
- **🏀 Team Analytics**: Team-specific performance, home/away splits, matchup analysis
- **💰 Betting History**: Complete betting history with profit/loss tracking

**Key Visualizations**:
- Win probability gauges and confidence indicators
- Calibration plots (predicted vs actual outcomes)
- Cumulative profit curves over time
- Performance breakdown by confidence level
- Interactive filtering and data export

See **[dashboard/README.md](dashboard/README.md)** for complete dashboard documentation.

### 🧪 Testing

Run the test suite:
```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# Database tests (requires USE_DATABASE=true)
pytest tests/test_database_integration.py -v

# Run specific test modules
pytest tests/test_error_handlers.py -v
pytest tests/test_migration_scripts.py -v
pytest tests/test_cli.py -v
```

**Test Coverage**:
- ✅ **Betting utilities** - Kelly Criterion, odds conversion, stake sizing, probability calibration
- ✅ **Team normalization** - All team code mappings and aliases
- ✅ **Data processing** - Rolling averages, preprocessing, target creation
- ✅ **Error handling** - Retry logic, validation, context managers, error recovery
- ✅ **Database integration** - CRUD operations, graceful CSV fallback
- ✅ **Logger infrastructure** - Logging configuration and output
- ✅ **CLI commands** - Command execution and argument parsing
- ✅ **Migration scripts** - CSV to PostgreSQL data migration

**CI/CD**: Automated testing on every push via GitHub Actions

### 📚 Documentation

- **[PROJECT.md](docs/PROJECT.md)** - Complete system overview and architecture
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Detailed technical documentation
- **[DATABASE_SETUP.md](docs/DATABASE_SETUP.md)** - Supabase/PostgreSQL setup guide
- **[ERROR_HANDLING.md](docs/ERROR_HANDLING.md)** - Error handling infrastructure
- **[database/README.md](database/README.md)** - Database migration quick reference

### 🤖 Automation

GitHub Actions workflows run daily at 06:00 UTC:
- Scrape previous day's games
- Generate predictions for today
- Calculate betting statistics
- Upload results as artifacts

### 🔒 Error Handling

Comprehensive error handling throughout:
- Automatic retries with exponential backoff
- Graceful fallbacks (database → CSV)
- Detailed logging with context
- Input validation and data checks
- Network failure recovery

---

## Database Migration (Optional)

To migrate existing CSV data to PostgreSQL:

```bash
# 1. Set up Supabase and apply schema
# See docs/DATABASE_SETUP.md for detailed instructions

# 2. Test migration (dry run)
python database/scripts/migrate_game_statistics.py --dry-run

# 3. Run migrations
python database/scripts/migrate_game_statistics.py
python database/scripts/migrate_predictions.py
python database/scripts/migrate_enriched_predictions.py
```

**Migration Features**:
- `--dry-run` preview without inserting data
- `--batch-size` control memory usage
- `--latest-only` migrate only recent files
- Automatic deduplication
- Comprehensive logging

---

## Project Structure

```
Basketball_prediction/
├── src/                          # Modern refactored codebase
│   ├── cli.py                    # Click CLI entry point (nba-predict command)
│   ├── commands/                 # CLI command implementations
│   │   ├── collect.py            # Data collection commands
│   │   ├── predict.py            # Prediction generation
│   │   ├── analyze.py            # Analysis & Kelly calculations
│   │   └── pipeline.py           # Complete workflow orchestration
│   ├── core/                     # Core business logic
│   │   ├── collector.py          # HistoricalGameCollector, UpcomingGameCollector
│   │   ├── predictor.py          # GameDataPreprocessor, MatchupBuilder, LightGBMPredictor
│   │   ├── analyzer.py           # BettingPerformanceAnalyzer, HomeWinRateCalculator
│   │   ├── betting.py            # OddsManager, ProbabilityCalibrator, KellyCriterion
│   │   └── constants.py          # Shared constants (team codes, Kelly defaults)
│   └── utils/                    # Utilities
│       ├── nba_utils.py          # Shared functions (team codes, dates, web scraping)
│       ├── logger.py             # Logging configuration
│       ├── error_handlers.py     # Error handling & retries
│       ├── db_utils.py           # Database operations
│       └── config_loader.py      # Configuration management
├── dashboard/                    # Streamlit web interface
│   ├── app.py                    # Home page
│   ├── pages/                    # Multi-page app (Today's Games, Performance, etc.)
│   ├── components/               # Reusable chart utilities
│   └── utils/                    # Data loading for dashboard
├── database/
│   ├── schemas/                  # PostgreSQL schema (8 tables, indexes, triggers)
│   └── scripts/                  # Migration scripts
├── output/                       # Generated data outputs
│   ├── Gathering_Data/           # Collected game data
│   │   ├── Whole_Statistic/      # Historical game CSVs
│   │   ├── Next_Game/            # Upcoming schedules
│   │   └── data/
│   │       ├── 2026_standings/   # Monthly schedule HTML
│   │       └── 2026_scores/      # Box score HTML
│   └── LightGBM/                 # Predictions & analysis outputs
├── docs/                         # Documentation
│   ├── PROJECT.md                # System overview & architecture
│   ├── ARCHITECTURE.md           # Technical design details
│   ├── DATABASE_SETUP.md         # Database configuration guide
│   └── ERROR_HANDLING.md         # Error handling infrastructure
├── tests/                        # Unit tests (pytest)
│   ├── test_betting_utils.py     # Kelly Criterion, odds conversion
│   ├── test_team_normalization.py # Team code mappings
│   ├── test_data_processing.py   # Rolling averages, preprocessing
│   ├── test_error_handlers.py    # Retry logic, validation
│   ├── test_database_integration.py # CRUD operations
│   ├── test_logger.py            # Logging configuration
│   ├── test_cli.py               # Command execution
│   └── test_migration_scripts.py # Data migration
├── .github/workflows/            # CI/CD automation
│   ├── daily_prediction_pipeline.yml  # Daily 06:00 UTC execution
│   └── tests.yml                 # Test automation
├── .env.example                  # Environment template
├── requirements.txt              # 23 dependencies
├── setup.py                      # CLI installation config
├── Dockerfile                    # Docker containerization
├── docker-compose.yml            # Multi-container setup
└── README.md                     # This file
```

---

## Technology Stack

- **Python 3.12** - Core language
- **LightGBM** - Machine learning
- **Selenium + BeautifulSoup** - Web scraping
- **pandas + numpy** - Data processing
- **PostgreSQL/Supabase** - Optional database (production)
- **pytest** - Testing framework
- **GitHub Actions** - Automation
- **The Odds API** - Live betting odds

---

## Contributing

See [PROJECT.md](docs/PROJECT.md) for detailed contribution guidelines and architecture documentation.

---

## License

MIT License - See LICENSE file for details

---

## Support

- **Documentation**: See `/docs` directory
- **Issues**: GitHub Issues
- **Database Setup**: [DATABASE_SETUP.md](docs/DATABASE_SETUP.md)
- **API Key**: https://the-odds-api.com/
