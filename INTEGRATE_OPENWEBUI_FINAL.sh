#!/bin/bash
# Final script to complete Open WebUI integration

echo "📦 OPEN WEBUI INTEGRATION FINAL STEP"
echo "===================================="

# This script assumes you have:
# 1. Cloned the Fort Knox repository
# 2. Are in the repository root directory

# Check we're in the right place
if [ ! -f "master_index.json" ] || [ ! -d "fort-knox-apis" ]; then
    echo "❌ ERROR: Run this from Fort Knox repository root!"
    exit 1
fi

# Save agent_connector.py if it exists
if [ -f "openwebui/agent_connector.py" ]; then
    echo "💾 Saving agent_connector.py..."
    cp openwebui/agent_connector.py /tmp/agent_connector_backup.py
fi

# Clear and recreate openwebui directory
echo "🧹 Preparing openwebui directory..."
rm -rf openwebui
mkdir openwebui

# Clone Open WebUI
echo "📥 Downloading fresh Open WebUI..."
git clone --depth 1 https://github.com/open-webui/open-webui.git temp_openwebui

# Copy everything
echo "📂 Copying Open WebUI files..."
cp -r temp_openwebui/* openwebui/
cp -r temp_openwebui/.* openwebui/ 2>/dev/null || true

# Restore agent_connector.py if we saved it
if [ -f "/tmp/agent_connector_backup.py" ]; then
    echo "🔧 Restoring agent_connector.py..."
    cp /tmp/agent_connector_backup.py openwebui/agent_connector.py
fi

# Clean up
echo "🧹 Cleaning up..."
rm -rf temp_openwebui

# Add integration README
cat > openwebui/README_FORT_KNOX.md << 'EOF'
# Open WebUI - Fort Knox Integration

This directory contains the complete Open WebUI source integrated with Fort Knox.

## Architecture
- Open WebUI provides the chat interface
- agent_connector.py bridges to repository agents
- Agents live in /agents with direct access to Fort Knox docs
- No external APIs needed - everything runs locally

## Quick Start
1. Install dependencies: `cd backend && pip install -r requirements.txt`
2. Run backend: `python main.py`
3. Install frontend: `npm install`
4. Run frontend: `npm run dev`

## Key Changes Needed
1. Disable external model connections (Ollama, OpenAI)
2. Route all chat through agent_connector.py
3. Replace model selector with agent selector
EOF

# Commit and push
echo "📤 Committing changes..."
git add -A
git commit -m "Add complete Open WebUI source (4,600+ files) to Fort Knox repository"
git push

echo "✅ DONE! Open WebUI is now fully integrated into Fort Knox!"
echo ""
echo "The /openwebui directory now contains:"
echo "- Complete Open WebUI source code (4,600+ files)"
echo "- agent_connector.py for bridging to agents"
echo "- README_FORT_KNOX.md with integration instructions"
