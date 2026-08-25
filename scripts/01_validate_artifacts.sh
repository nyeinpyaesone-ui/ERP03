#!/bin/bash
set -e

# =============================================================================
# STEP 1: ARTIFACT VALIDATION
# Validates integrity of build artifacts before deployment
# =============================================================================

echo "🔍 Step 1: Artifact Validation"

VALIDATION_PASSED=true

# Check critical directories exist
DIRS=("ERP-BACKEND/app" "AI-BACKEND/src" "INTEGRATION" "frontend-mrp/src")
for dir in "${DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        echo "❌ Missing directory: $dir"
        VALIDATION_PASSED=false
    else
        echo "✅ Directory exists: $dir"
    fi
done

# Check critical files exist
FILES=(
    "ERP-BACKEND/requirements.txt"
    "ERP-BACKEND/Dockerfile"
    "AI-BACKEND/requirements.txt"
    "AI-BACKEND/Dockerfile"
    "docker-compose.prod.yml"
    ".env.example"
)

for file in "${FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Missing file: $file"
        VALIDATION_PASSED=false
    else
        echo "✅ File exists: $file"
    fi
done

# Validate Python syntax
echo "🐍 Validating Python syntax..."
python3 -m py_compile ERP-BACKEND/app/main.py || VALIDATION_PASSED=false
python3 -m py_compile AI-BACKEND/src/main.py || VALIDATION_PASSED=false

# Validate Docker Compose syntax
echo "🐳 Validating Docker Compose syntax..."
docker-compose -f docker-compose.prod.yml config > /dev/null || VALIDATION_PASSED=false

if [ "$VALIDATION_PASSED" = false ]; then
    echo "❌ Artifact validation FAILED"
    exit 1
fi

echo "✅ Artifact validation PASSED"
