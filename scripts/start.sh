#!/bin/bash
set -e

echo "======================================"
echo " Running Yoyo Migrations..."
echo "======================================"

# Run yoyo migrations using environment variables
yoyo apply --batch --database "postgresql://${DB_USER:-postgres}:${DB_PASSWORD:-haidercpp}@${DB_HOST:-db}:${DB_PORT:-5432}/${DB_NAME:-shiftmaster_dbsm}" ./migrations

echo "======================================"
echo " Starting the Application..."
echo "======================================"

# Execute the main command (uvicorn)
exec "$@"
