#!/bin/bash

# AIronman 42-Day Data Sync Wrapper
# This script runs the 42-day data sync to establish CTL calculation foundation

echo "🚀 Starting AIronman 42-Day Data Sync..."
echo "This will download the last 42 days of workouts and health data"
echo "to establish the foundation for CTL calculation."
echo ""

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: Please run this script from the AIronman project root directory"
    exit 1
fi

# Check if containers are running
if ! docker compose ps | grep -q "backend.*Up"; then
    echo "⚠️  Warning: Backend container is not running."
    echo "   The script will still work but may be slower without the containerized environment."
    echo ""
fi

# Run the Python script
echo "📥 Running 42-day data sync..."
python3 scripts/sync_42_days.py

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 42-day sync completed successfully!"
    echo "You can now implement CTL calculation with this data foundation."
else
    echo ""
    echo "❌ 42-day sync failed. Check the logs for details."
    exit 1
fi 