#!/bin/bash
set -e

# =============================================================================
# STEP 2: ENVIRONMENT RESOLUTION
# Resolves and validates environment configuration
# =============================================================================

echo "🔧 Step 2: Environment Resolution"

ENV_FILE=".env"
ENV_EXAMPLE=".env.example"

# Create .env from .env.example if it doesn't exist
if [ ! -f "$ENV_FILE" ]; then
    echo "⚠️  $ENV_FILE not found, creating from $ENV_EXAMPLE..."
    cp "$ENV_EXAMPLE" "$ENV_FILE"
    echo "✅ Created $ENV_FILE from template"
    
    # Generate secure secrets
    echo "🔐 Generating secure secrets..."
    
    # Generate SECRET_KEY for ERP-BACKEND
    SECRET_KEY=$(openssl rand -hex 32)
    sed -i "s/your-secret-key-here/$SECRET_KEY/" "$ENV_FILE"
    
    # Generate JWT_SECRET
    JWT_SECRET=$(openssl rand -hex 32)
    sed -i "s/your-jwt-secret-here/$JWT_SECRET/" "$ENV_FILE"
    
    # Generate DATABASE_PASSWORD
    DB_PASSWORD=$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9')
    sed -i "s/change-this-password/$DB_PASSWORD/" "$ENV_FILE"
    
    echo "✅ Secure secrets generated"
else
    echo "✅ $ENV_FILE already exists"
fi

# Validate required environment variables
echo "📋 Validating environment variables..."

REQUIRED_VARS=(
    "DATABASE_URL"
    "SECRET_KEY"
    "JWT_SECRET"
    "REDIS_URL"
    "ERP_API_URL"
    "AI_API_URL"
)

MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
    if ! grep -q "^$var=" "$ENV_FILE"; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    echo "❌ Missing required environment variables:"
    for var in "${MISSING_VARS[@]}"; do
        echo "   - $var"
    done
    exit 1
fi

echo "✅ All required environment variables present"

# Export environment variables
set -a
source "$ENV_FILE"
set +a

echo "✅ Environment resolution completed"
