#!/bin/bash
# Run this script to push BoostSuite to GitHub
# Usage: bash PUSH_TO_GITHUB.sh

cd /home/darko/.openclaw/workspace/boostsuite

echo "📦 Pushing BoostSuite to GitHub..."
echo ""

# Try pushing with SSH
echo "Attempting push with SSH key..."
GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed25519" git push github master 2>&1

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully pushed to GitHub!"
    echo "🔗 https://github.com/Maxkrempl/AIboost"
else
    echo ""
    echo "❌ Push failed. You may need to:"
    echo "   1. Enter your SSH key passphrase when prompted"
    echo "   2. Or set up a GitHub personal access token"
    echo ""
    echo "To set up a token:"
    echo "   1. Go to https://github.com/settings/tokens"
    echo "   2. Generate a new token with 'repo' scope"
    echo "   3. Run: git remote set-url github https://<YOUR_TOKEN>@github.com/Maxkrempl/AIboost.git"
    echo "   4. Then run this script again"
fi
