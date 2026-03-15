#!/bin/bash

# BestFam Framework Orchestrator
# Goal: Standardized GitOps deployment with SOPS Secret Management

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

export SOPS_AGE_KEY_FILE=~/.sops_age_key.txt

echo "=========================================="
echo "🚀 BestFam GitOps Pipeline: Hard Sync"
echo "=========================================="

# 1. DECRYPT: Unlock Secrets (SOPS)
echo -n "[1/4] Decrypting Secrets (SOPS)... "
FILES_TO_DECRYPT=("shared-services/.env" "apps/betting-prod/.env" "apps/betting-dev/.env")

for file in "${FILES_TO_DECRYPT[@]}"; do
    if [ -f "$file" ] && grep -q "sops_version" "$file"; then
        sops --decrypt --in-place "$file"
    fi
done
echo -e "${GREEN}DONE${NC}"

# 2. DEPLOY: Update Containers
SERVICES=("shared-services" "apps/betting-prod" "apps/betting-dev")

for dir in "${SERVICES[@]}"; do
    echo -e "${YELLOW}[2/4] Updating: $dir...${NC}"
    if [ -d "$dir" ]; then
        cd "$dir"
        docker compose build --pull --quiet
        docker compose up -d --force-recreate --remove-orphans
        cd - > /dev/null
        echo -e "${GREEN}DONE: $dir is live.${NC}"
    else
        echo -e "${RED}ERROR: Directory $dir not found!${NC}"
    fi
done

# 3. ENCRYPT: Relock Secrets
echo -n "[3/4] Encrypting Secrets (SOPS)... "
for file in "${FILES_TO_DECRYPT[@]}"; do
    if [ -f "$file" ] && ! grep -q "sops_version" "$file"; then
        sops --encrypt --in-place "$file"
    fi
done
echo -e "${GREEN}DONE${NC}"

echo "=========================================="
echo "✅ DEPLOYMENT COMPLETE"
echo "=========================================="

# 4. SERVICES: Start/Restart Background Agents
echo -n "[4/5] Starting Chat Bridge... "
pkill -f chat_bridge.py || true
# Ensure DB_HOST is set to localhost for host-based execution
export DB_HOST=localhost
nohup /Users/grantbest/Documents/Active/venv/bin/python3 scripts/chat_bridge.py > scripts/chat_bridge.log 2>&1 &
echo -e "${GREEN}DONE${NC}"

# 5. Validation: Health Checks and Regression Tests
echo "[5/5] Running Validation..."
./tests/validate-homelab.sh

echo "------------------------------------------"
echo "🎭 Running Playwright Regression Tests..."
npx playwright test --project=chromium
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ ALL REGRESSION TESTS PASSED${NC}"
else
    echo -e "${RED}❌ REGRESSION TESTS FAILED${NC}"
fi

echo "------------------------------------------"
echo "🤖 Running Agentic AI Audit..."
PYTHONPATH=scripts ./venv/bin/python3 tests/agentic_validation.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ AGENTIC AI AUDIT PASSED${NC}"
else
    echo -e "${RED}❌ AGENTIC AI AUDIT FAILED${NC}"
fi

echo "=========================================="
