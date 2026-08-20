#!/bin/bash
# Git pre-push security check — MORA biti izveden PRED vsakim pushom
# Usage: bash tools/git-pre-push-check.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🔒 Git pre-push security check..."
echo ""

# 1. Check what would be committed
echo "📋 Files staged for commit:"
git diff --cached --name-only 2>/dev/null || git diff --name-only
echo ""

# 2. Scan for secrets in staged/tracked files
echo "🔍 Scanning for secrets..."
SECRET_FOUND=0

PATTERNS="sk_live_|sk_test_|sk-[0-9a-f]{20,}|gsk_|glpat-|re_[A-Za-z0-9]|nfp_|tvly-|AKIA|AIza|secret_key.*=.*['\"]|api_key.*=.*['\"]|password.*=.*['\"]|AUTH_TOKEN|DEEPSEEK_API_KEY|OPENROUTER_API_KEY|STRIPE_SECRET"

# Check staged files
if git diff --cached --name-only 2>/dev/null | xargs grep -l -E "$PATTERNS" 2>/dev/null; then
    echo -e "${RED}❌ SECRETS FOUND IN STAGED FILES!${NC}"
    SECRET_FOUND=1
fi

# Check tracked files
if git ls-files | xargs grep -l -E "$PATTERNS" 2>/dev/null; then
    echo -e "${RED}❌ SECRETS FOUND IN TRACKED FILES!${NC}"
    SECRET_FOUND=1
fi

# 3. Check for dangerous file types
echo ""
echo "📁 Checking for dangerous file types..."
DANGEROUS_FILES=$(git ls-files | grep -E "(\.log$|error_log|\.backup$|\.bak$|config\.php$|stripe-config|\.env|credentials|secrets/)" 2>/dev/null)

if [ -n "$DANGEROUS_FILES" ]; then
    echo -e "${RED}❌ DANGEROUS FILES TRACKED:${NC}"
    echo "$DANGEROUS_FILES"
    SECRET_FOUND=1
fi

# 4. Result
echo ""
if [ $SECRET_FOUND -eq 1 ]; then
    echo -e "${RED}🚨 PUSH BLOCKED — Remove secrets before pushing!${NC}"
    echo "Run: git rm --cached <file> for each dangerous file"
    exit 1
else
    echo -e "${GREEN}✅ No secrets detected. Safe to push.${NC}"
    exit 0
fi
