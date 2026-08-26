#!/bin/bash
set -e

# =============================================================================
# STEP 3: PACKAGE STRUCTURE REPAIR
# Ensures all package structures are correct and dependencies installed
# =============================================================================

echo "📦 Step 3: Package Structure Repair"

# Repair ERP-BACKEND structure
echo "🔧 Repairing ERP-BACKEND structure..."

# Ensure __init__.py files exist
INIT_FILES=(
    "ERP-BACKEND/app/__init__.py"
    "ERP-BACKEND/app/api/__init__.py"
    "ERP-BACKEND/app/api/v1/__init__.py"
    "ERP-BACKEND/app/core/__init__.py"
    "ERP-BACKEND/app/models/__init__.py"
    "ERP-BACKEND/app/schemas/__init__.py"
    "ERP-BACKEND/app/services/__init__.py"
    "ERP-BACKEND/app/db/__init__.py"
)

for init_file in "${INIT_FILES[@]}"; do
    if [ ! -f "$init_file" ]; then
        echo "   Creating $init_file"
        touch "$init_file"
    fi
done

echo "✅ ERP-BACKEND structure repaired"

# Repair AI-BACKEND structure
echo "🔧 Repairing AI-BACKEND structure..."

AI_INIT_FILES=(
    "AI-BACKEND/src/__init__.py"
    "AI-BACKEND/src/api/__init__.py"
    "AI-BACKEND/src/core/__init__.py"
    "AI-BACKEND/src/agents/__init__.py"
    "AI-BACKEND/src/services/__init__.py"
)

for init_file in "${AI_INIT_FILES[@]}"; do
    if [ ! -f "$init_file" ]; then
        echo "   Creating $init_file"
        touch "$init_file"
    fi
done

echo "✅ AI-BACKEND structure repaired"

# Install Python dependencies
echo "🐍 Installing Python dependencies..."

cd ERP-BACKEND
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet
    echo "✅ ERP-BACKEND dependencies installed"
else
    echo "⚠️  requirements.txt not found in ERP-BACKEND"
fi
cd ..

cd AI-BACKEND
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet
    echo "✅ AI-BACKEND dependencies installed"
else
    echo "⚠️  requirements.txt not found in AI-BACKEND"
fi
cd ..

# Install Node.js dependencies for frontend modules
echo "📦 Installing Node.js dependencies..."

FRONTEND_DIRS=("frontend-mrp" "frontend-ecommerce" "frontend-pos" "frontend-bi")

for dir in "${FRONTEND_DIRS[@]}"; do
    if [ -d "$dir" ] && [ -f "$dir/package.json" ]; then
        echo "   Installing dependencies for $dir..."
        cd "$dir"
        npm install --silent
        cd ..
        echo "✅ $dir dependencies installed"
    else
        echo "⚠️  Skipping $dir (no package.json)"
    fi
done

echo "✅ Package structure repair completed"
