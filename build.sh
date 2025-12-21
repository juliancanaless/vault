#!/usr/bin/env bash
# The Vault - Render Build Script
# This script runs during the build phase on Render.com

set -o errexit  # Exit on error

echo "🔐 Building The Vault..."

# Install Python dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --no-input

# Run database migrations
echo "🗄️ Running migrations..."
python manage.py migrate

echo "✅ Build complete!"

