#!/bin/bash
set -e 

DB_FILE="/app/bitcoin_daily_data.db"
PROJECT_ROOT_IN_CONTAINER="/app"
SEED_MARKER_FILE="${PROJECT_ROOT_IN_CONTAINER}/.db_seeded_marker"

# Ensure we are in the project root inside the container
cd "$PROJECT_ROOT_IN_CONTAINER"

echo "Entrypoint: Current directory: $(pwd)"
echo "Entrypoint: Checking for database and seed status..."

# 1. Initialize DB Schema (using the Python utility directly)
echo "Entrypoint: Initializing database schema..."
python -c "from backend.db_utils import init_db; print('Python: Calling init_db()'); init_db()"
# The backend/main.py will also call init_db on startup, this is just for explicit ordering if needed.

NEEDS_SEEDING=false
if [ ! -f "$SEED_MARKER_FILE" ]; then
    echo "Entrypoint: Seed marker file '$SEED_MARKER_FILE' not found. Database will be seeded."
    NEEDS_SEEDING=true
else
    echo "Entrypoint: Seed marker file found. Assuming database is already seeded."
fi

if [ "$NEEDS_SEEDING" = true ]; then
    echo "Entrypoint: Seeding data..."
    
    # 2. Import CSV data
    echo "Entrypoint: Importing CSV data (running scripts/csv_importer.py)..."
    if python scripts/csv_importer.py; then
        echo "Entrypoint: CSV import SUCCEEDED."
    else
        echo "Entrypoint: CSV import FAILED. Check logs."
        # Decide on error handling: exit or continue? For now, continue.
    fi

    # 3. Run main manual data filler
    echo "Entrypoint: Running main manual data filler (running scripts/manual_data_filler.py)..."
    if python scripts/manual_data_filler.py; then
        echo "Entrypoint: Main manual data fill SUCCEEDED."
    else
        echo "Entrypoint: Main manual data fill FAILED. Check logs."
    fi
    
    # 4. Run specific manual data filler
    echo "Entrypoint: Running specific manual data filler (running scripts/fill-in-20240331.py)..."
    if python scripts/fill-in-20240331.py; then
        echo "Entrypoint: Specific manual data fill SUCCEEDED."
    else
        echo "Entrypoint: Specific manual data fill FAILED. Check logs."
    fi
    
    echo "Entrypoint: Data seeding process complete."
    touch "$SEED_MARKER_FILE" 
    echo "Entrypoint: Seed marker file created at $SEED_MARKER_FILE."
else
    echo "Entrypoint: Skipping data seed."
fi

echo "Entrypoint: Starting Flask application (executing CMD: $@)..."
exec "$@" 