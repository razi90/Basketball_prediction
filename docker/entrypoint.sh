#!/bin/bash
set -e

echo "==================================================================="
echo "NBA Prediction App - Starting..."
echo "==================================================================="

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" > /dev/null 2>&1; then
        echo "✅ Database is ready!"
        break
    fi

    attempt=$((attempt + 1))
    echo "   Attempt $attempt/$max_attempts - Database not ready yet..."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Database connection timeout after $max_attempts attempts"
    exit 1
fi

# Check if we should initialize the database
if [ "${SKIP_DB_INIT}" != "true" ]; then
    echo ""
    echo "🔍 Checking if database needs initialization..."

    # Run database initialization script
    python /app/database/scripts/init_database.py --force

    if [ $? -eq 0 ]; then
        echo "✅ Database initialization complete"
    else
        echo "⚠️  Database initialization had issues, but continuing..."
    fi
else
    echo "⏭️  Skipping database initialization (SKIP_DB_INIT=true)"
fi

echo ""
echo "==================================================================="
echo "🚀 Starting application..."
echo "==================================================================="

# Execute the main command
exec "$@"
