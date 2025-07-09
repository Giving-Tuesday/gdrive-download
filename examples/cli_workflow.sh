#!/bin/bash
# 
# Example CLI workflow for GivingTuesday AAR Tools
# 
# This script demonstrates how to use the command-line tools
# to download, convert, and analyze AAR documents.
#

set -e  # Exit on any error

echo "🚀 GivingTuesday AAR Analysis Workflow"
echo "======================================"

# Configuration
FOLDER_URL="https://drive.google.com/drive/folders/YOUR_FOLDER_ID"
DOWNLOADS_DIR="workflow_downloads"
MARKDOWN_DIR="workflow_markdown"
REPORTS_DIR="workflow_reports"
CREDENTIALS_FILE="credentials.json"

# Step 1: Download and convert files
echo ""
echo "📥 Step 1: Downloading and converting files..."
echo "----------------------------------------------"

aar-download \
    --folder-url "$FOLDER_URL" \
    --output-dir "$DOWNLOADS_DIR" \
    --markdown-dir "$MARKDOWN_DIR" \
    --credentials "$CREDENTIALS_FILE" \
    --convert \
    --track-relationships \
    --log-level INFO

echo "✅ Download and conversion complete!"

# Step 2: Generate all analysis reports
echo ""
echo "🔍 Step 2: Analyzing content and generating reports..."
echo "----------------------------------------------------"

aar-analyze \
    --input-dir "$MARKDOWN_DIR" \
    --output-dir "$REPORTS_DIR" \
    --report-type all \
    --url-mappings file_relationships.csv \
    --save-analysis \
    --log-level INFO

echo "✅ Analysis complete!"

# Step 3: Check status and manage files
echo ""
echo "📊 Step 3: Checking status..."
echo "----------------------------"

aar-manage status \
    --downloads-dir "$DOWNLOADS_DIR" \
    --markdown-dir "$MARKDOWN_DIR" \
    --url-mappings file_relationships.csv

# Step 4: Show results
echo ""
echo "📋 Step 4: Results summary..."
echo "----------------------------"

echo "Generated reports:"
ls -la "$REPORTS_DIR"/*.md 2>/dev/null || echo "No reports found"

echo ""
echo "Analysis data files:"
ls -la "$REPORTS_DIR"/*.json 2>/dev/null || echo "No analysis files found"

echo ""
echo "🎉 Workflow complete!"
echo ""
echo "Next steps:"
echo "  • Review the generated reports in $REPORTS_DIR/"
echo "  • Share insights with your team"
echo "  • Use findings to improve future operations"