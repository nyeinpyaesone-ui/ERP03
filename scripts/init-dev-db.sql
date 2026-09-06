#!/bin/bash
# Initialize development database with test data
# This script runs automatically when the PostgreSQL container starts

set -e

echo "🚀 Initializing ERP Development Database..."

# Create extensions
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Enable useful extensions
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pg_trgm";
    
    -- Create schema for testing
    CREATE SCHEMA IF NOT EXISTS test_schema;
    
    -- Grant privileges
    GRANT ALL PRIVILEGES ON SCHEMA test_schema TO ${POSTGRES_USER};
    GRANT ALL PRIVILEGES ON DATABASE ${POSTGRES_DB} TO ${POSTGRES_USER};
EOSQL

echo "✅ Database initialization complete!"
echo "📊 Database: ${POSTGRES_DB}"
echo "👤 User: ${POSTGRES_USER}"
echo "🔗 Connection: postgresql://${POSTGRES_USER}@localhost:5432/${POSTGRES_DB}"
