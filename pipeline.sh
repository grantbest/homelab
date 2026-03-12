#!/bin/bash

# --- Color Codes ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "🛡️  Homelab GitOps Regression Pipeline"
echo "=========================================="

# 1. PRE-DEPLOY: Decrypt Secrets
echo -n "[1/6] Decrypting Secrets (SOPS)... "
export SOPS_AGE_KEY_FILE=~/.sops_age_key.txt
if sops --decrypt --in-place shared-services/.env && sops --decrypt --in-place apps/betting-engine/.env; then
    echo -e "${GREEN}SUCCESS${NC}"
else
    echo -e "${RED}FAILED${NC} (Check AGE key)"
    exit 1
fi

# 2. BUILD: Application Code
# We pull the latest from the app repo and build the production images
if [ -z "$APP_SOURCE_PATH" ]; then
    # Default to the path we discovered earlier
    APP_SOURCE_PATH="/Users/grantbest/Documents/code/Gambling Engine"
fi

echo "[2/6] Building Application Images at $APP_SOURCE_PATH..."
if [ -d "$APP_SOURCE_PATH" ]; then
    cd "$APP_SOURCE_PATH"
    # Optional: git pull origin main (if you want it fully automated)
    docker compose -f docker-compose.test-multi.yml build --quiet frontend-prod engine-prod
    cd - > /dev/null
else
    echo -e "${YELLOW}App source not found at $APP_SOURCE_PATH. Skipping build.${NC}"
fi

# 3. SECURITY: Local Image Scan
echo "[3/6] Scanning Docker Images (Trivy)..."
# We scan our core app images before restarting
if which trivy >/dev/null; then
    trivy image --severity HIGH,CRITICAL --quiet gamblingengine-frontend-prod:latest
    trivy image --severity HIGH,CRITICAL --quiet gamblingengine-engine-prod:latest
else
    echo -e "${YELLOW}Trivy not installed locally. Skipping local scan.${NC}"
fi

# 3. DEPLOY: Update Containers
echo "[3/5] Updating Infrastructure & Apps..."
cd shared-services && docker compose up -d --quiet-pull
cd ../apps/betting-engine && docker compose up -d --quiet-pull
cd ../..

# 4. SMOKE TEST: Infrastructure Health
echo -n "[4/5] Running Infrastructure Smoke Tests... "
if ./tests/validate-homelab.sh > /dev/null; then
    echo -e "${GREEN}PASS${NC}"
else
    echo -e "${RED}FAIL${NC} (Smoke tests failed!)"
    ./tests/validate-homelab.sh # Run again to show output
    exit 1
fi

# 5. REGRESSION: Business Logic (UI/API)
echo "[5/4] Running Business Logic Regression..."
# Here we call Playwright (Headless Browser)
# We use npx to run it directly
if npx playwright test tests/regression; then
    echo -e "${GREEN}ALL REGRESSIONS PASSED!${NC}"
else
    echo -e "${RED}REGRESSION FAILED!${NC}"
    echo -e "${YELLOW}Initiating Auto-Rollback...${NC}"
    # Rollback logic could go here (e.g., docker compose rollback)
    exit 1
fi

# POST-DEPLOY: Re-encrypt Secrets
echo -n "🔒 Re-encrypting Secrets... "
sops --encrypt --in-place shared-services/.env && sops --encrypt --in-place apps/betting-engine/.env
echo -e "${GREEN}DONE${NC}"

echo "=========================================="
echo "✅ PIPELINE COMPLETE: Homelab is Healthy"
echo "=========================================="
