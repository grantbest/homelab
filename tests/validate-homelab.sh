#!/bin/bash

# --- Color Codes ---
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo "=========================================="
echo "🚀 Homelab GitOps Validation Suite"
echo "=========================================="

# 1. Check if Shared Services are running
echo -n "[1/5] Checking Shared Services... "
SERVICES=("traefik" "cloudflared" "postgres" "redis")
MISSING_SERVICES=()

for svc in "${SERVICES[@]}"; do
    if ! docker ps --format '{{.Names}}' | grep -q "^$svc$"; then
        MISSING_SERVICES+=("$svc")
    fi
done

if [ ${#MISSING_SERVICES[@]} -eq 0 ]; then
    echo -e "${GREEN}PASS${NC}"
else
    echo -e "${RED}FAIL${NC} (Missing: ${MISSING_SERVICES[*]})"
    exit 1
fi

# 2. Check Global Network Connectivity
echo -n "[2/5] Checking homelab_global network... "
if docker network inspect homelab_global >/dev/null 2>&1; then
    echo -e "${GREEN}PASS${NC}"
else
    echo -e "${RED}FAIL${NC} (Network homelab_global not found)"
    exit 1
fi

# 3. Check Database Connectivity
echo -n "[3/5] Testing PostgreSQL Connection... "
if docker exec postgres pg_isready -U postgres >/dev/null 2>&1; then
    echo -e "${GREEN}PASS${NC}"
else
    echo -e "${RED}FAIL${NC}"
fi

# 4. Check Redis Connectivity
echo -n "[4/5] Testing Redis Connection... "
if docker exec redis redis-cli ping | grep -q "PONG"; then
    echo -e "${GREEN}PASS${NC}"
else
    echo -e "${RED}FAIL${NC}"
fi

# 5. Check Application Routing (Traefik API)
echo -n "[5/5] Checking Traefik Routing Status... "
ROUTERS=$(curl -s http://localhost:8080/api/http/routers)
EXPECTED_ROUTERS=("betting-dashboard@docker" "dev-app-secure@file")
FAIL_ROUTERS=()

for router in "${EXPECTED_ROUTERS[@]}"; do
    if ! echo "$ROUTERS" | grep -q "$router"; then
        FAIL_ROUTERS+=("$router")
    fi
done

if [ ${#FAIL_ROUTERS[@]} -eq 0 ]; then
    echo -e "${GREEN}PASS${NC}"
else
    echo -e "${RED}FAIL${NC} (Missing routers: ${FAIL_ROUTERS[*]})"
fi

# 6. Run App-Specific Validations
echo "=========================================="
echo "📱 Running App-Specific Validations"
echo "=========================================="

# Find all validate.sh files in the apps directory
APP_TESTS=$(find apps -name "validate.sh")

if [ -z "$APP_TESTS" ]; then
    echo "No app-specific tests found."
else
    for test_script in $APP_TESTS; do
        APP_NAME=$(dirname "$test_script" | xargs basename)
        echo -n "Testing App: [$APP_NAME]... "
        chmod +x "$test_script"
        if bash "$test_script"; then
            echo -e "${GREEN}PASS${NC}"
        else
            echo -e "${RED}FAIL${NC}"
            exit 1
        fi
    done
fi

echo "=========================================="
echo "✅ All core and app tests complete!"
echo "=========================================="
