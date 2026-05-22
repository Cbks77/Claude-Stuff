#!/usr/bin/env bash
# =============================================================
# Composio CLI Setup Script
# Workspace: curtisbrooks77_workspace
# =============================================================

set -e

echo "🚀 Installing Composio CLI..."

# Install via pip in a virtual environment (recommended)
python3 -m venv composio-env
source composio-env/bin/activate

pip install composio-core --quiet

echo "✅ Composio installed: $(composio --version)"

# Configure API key
echo "🔑 Configuring API key..."
COMPOSIO_API_KEY="uak_75L-MQdUUANwBscpDuWo"

# Set via environment variable (add to your .bashrc or .zshrc)
export COMPOSIO_API_KEY="uak_75L-MQdUUANwBscpDuWo"

echo ""
echo "✅ Setup complete! Useful commands:"
echo ""
echo "  composio whoami            # Verify your identity"
echo "  composio apps              # List all available integrations"
echo "  composio add github        # Connect GitHub account"
echo "  composio add slack         # Connect Slack account"
echo "  composio add gmail         # Connect Gmail account"
echo "  composio connections       # View active connections"
echo "  composio triggers          # Manage event triggers"
echo "  composio actions           # Browse available actions"
echo ""
echo "To persist your API key, add this to your shell profile:"
echo "  export COMPOSIO_API_KEY=\"uak_75L-MQdUUANwBscpDuWo\""
echo ""
echo "Python SDK usage:"
echo "  from composio import ComposioToolSet"
echo "  toolset = ComposioToolSet(api_key='uak_75L-MQdUUANwBscpDuWo')"
