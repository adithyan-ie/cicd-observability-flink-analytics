#!/usr/bin/env bash
# Quick Start Script - Run DORA Metrics Dashboard with Sample Data
# Usage: bash quickstart.sh

echo "🚀 Smart Incident Platform - DORA Metrics Quick Start"
echo "======================================================"
echo ""

# Check if running from correct directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: Run this script from smart-incident-platform/ directory"
    exit 1
fi

echo "📦 Installing dependencies..."
pip install -q -r requirements.txt

echo "📝 Generating sample CI/CD pipeline data..."
python sample_data.py

echo ""
echo "✅ Setup complete!"
echo ""
echo "Now run: python app.py"
echo ""
echo "Then visit:"
echo "  • http://localhost:5000/dora          (DORA Metrics Dashboard)"
echo "  • http://localhost:5000/               (Main Dashboard)"
echo "  • http://localhost:5000/incidents      (Incidents)"
echo ""
echo "📚 For more info, see:"
echo "  • DORA_README.md    - Complete documentation"
echo "  • API_DOCS.md       - API reference and integration examples"
echo ""
echo "🧪 Test the API:"
echo "  python test_client.py success my-pipeline run-001"
echo "  python test_client.py metrics"
