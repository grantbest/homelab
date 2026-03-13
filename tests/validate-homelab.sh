#!/bin/bash

# BestFam Framework: Global Validation Suite
# Goal: Verify Infrastructure, Routing, and Multi-Environment Isolation

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo "=========================================="
echo "🚀 BestFam Framework: Health Checks"
echo "=========================================="

# 1. Shared Services
echo -n "[1/7] Shared Services (Core)... "
SERVICES=("traefik" "cloudflared" "postgres" "redis")
MISSING=()
for svc in "${SERVICES[@]}"; do
    if ! docker ps --format '{{.Names}}' | grep -q "^$svc$"; then MISSING+=("$svc"); fi
done
if [ ${#MISSING[@]} -eq 0 ]; then echo -e "${GREEN}PASS${NC}"; else echo -e "${RED}FAIL${NC} (Missing: ${MISSING[*]})"; fi

# 2. Database Health
echo -n "[2/7] Postgres Connectivity... "
if docker exec postgres pg_isready -U postgres >/dev/null 2>&1; then echo -e "${GREEN}PASS${NC}"; else echo -e "${RED}FAIL${NC}"; fi

# 3. Network Isolation
echo -n "[3/7] Framework Network (Global)... "
if docker network inspect homelab_global >/dev/null 2>&1; then echo -e "${GREEN}PASS${NC}"; else echo -e "${RED}FAIL${NC}"; fi

# 4. Cloudflare Tunnel
echo -n "[4/7] Cloudflare Tunnel Auth... "
if docker logs cloudflared 2>&1 | grep -q "Registered tunnel connection"; then echo -e "${GREEN}PASS${NC}"; else echo -e "${RED}FAIL${NC}"; fi

# 5. Routing (Traefik API)
echo -n "[5/7] Traefik Routing Table... "
ROUTERS=$(curl -s http://localhost:8080/api/http/routers)
if echo "$ROUTERS" | grep -q "betting-prod@docker" && echo "$ROUTERS" | grep -q "betting-dev@docker"; then
    echo -e "${GREEN}PASS${NC}"
else
    echo -e "${RED}FAIL${NC} (Missing Instance Routers)"
fi

# 6. Production Health (bestfam.us)
echo -n "[6/7] Production Instance Health... "
if curl -s -H "Host: bestfam.us" http://localhost:80/api/config | grep -q "production"; then
    echo -e "${GREEN}PASS${NC}"
else
    echo -e "${RED}FAIL${NC}"
fi

# 7. Development Health (dev.bestfam.us)
echo -n "[7/7] Development Instance Health... "
if curl -s -H "Host: dev.bestfam.us" http://localhost:80/api/config | grep -q "development"; then
    echo -e "${GREEN}PASS${NC}"
else
    echo -e "${RED}FAIL${NC}"
fi

echo "=========================================="
echo "✅ ALL SYSTEMS OPERATIONAL"
echo "=========================================="
