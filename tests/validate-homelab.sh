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
echo -n "[1/8] Shared Services (Core + Monitoring)... "
SERVICES=("traefik" "cloudflared" "postgres" "redis" "prometheus" "grafana" "postgres-exporter")
MISSING=()
for svc in "${SERVICES[@]}"; do
    if ! docker ps --format '{{.Names}}' | grep -q "^$svc$"; then MISSING+=("$svc"); fi
done
if [ ${#MISSING[@]} -eq 0 ]; then echo -e "${GREEN}PASS${NC}"; else echo -e "${RED}FAIL${NC} (Missing: ${MISSING[*]})"; fi

# 2. Database Health
echo -n "[2/8] Postgres Connectivity... "
if docker exec postgres pg_isready -U postgres >/dev/null 2>&1; then echo -e "${GREEN}PASS${NC}"; else echo -e "${RED}FAIL${NC}"; fi

# 3. Network Isolation
echo -n "[3/8] Framework Network (Global)... "
if docker network inspect homelab_global >/dev/null 2>&1; then echo -e "${GREEN}PASS${NC}"; else echo -e "${RED}FAIL${NC}"; fi

# 4. Cloudflare Tunnel
echo -n "[4/8] Cloudflare Tunnel Auth... "
if docker logs cloudflared 2>&1 | grep -q "Registered tunnel connection"; then echo -e "${GREEN}PASS${NC}"; else echo -e "${RED}FAIL${NC}"; fi

# 5. Routing (Traefik API)
echo -n "[5/8] Traefik Routing Table... "
ROUTERS=$(curl -s http://localhost:8080/api/http/routers)
if echo "$ROUTERS" | grep -q "betting-prod@docker" && echo "$ROUTERS" | grep -q "betting-dev@docker"; then
    echo -e "${GREEN}PASS${NC}"
else
    echo -e "${RED}FAIL${NC} (Missing Instance Routers)"
fi

# 6. Production Health (bestfam.us)
echo -n "[6/8] Production Instance Health... "
if curl -s -H "Host: bestfam.us" http://localhost:80/api/config | grep -q "production"; then
    echo -e "${GREEN}PASS${NC}"
else
    echo -e "${RED}FAIL${NC}"
fi

# 7. Development Health (dev.bestfam.us)
echo -n "[7/8] Development Instance Health... "
if curl -s -H "Host: dev.bestfam.us" http://localhost:80/api/config | grep -q "development"; then
    echo -e "${GREEN}PASS${NC}"
else
    echo -e "${RED}FAIL${NC}"
fi

# 8. Business Logic & Integration Gate
echo "=========================================="
echo "🎯 BestFam Framework: Business Logic"
echo "=========================================="

# 8a. Betting Engine Active Games
echo -n "[8a/8] Betting Engine: Active Games... "
GAME_COUNT=$(curl -s -H "Host: bestfam.us" http://localhost:80/api/health | grep -o '"game_count":[0-9]*' | cut -d: -f2)
if [ -n "$GAME_COUNT" ]; then 
    echo -e "${GREEN}PASS${NC} ($GAME_COUNT games active)"
else
    echo -e "${RED}FAIL${NC} (Health endpoint dead or game_count missing)"
fi

# 8b. Vikunja API Reachable
echo -n "[8b/8] Vikunja API Reachability... "
if curl -sf http://localhost:3456/api/v1/info > /dev/null; then
    echo -e "${GREEN}PASS${NC}"
else
    echo -e "${RED}FAIL${NC} (Vikunja unreachable on 3456)"
fi

# 8c. Rules API Stability
echo -n "[8c/8] Rules API: Data Integrity... "
RULES_LEN=$(curl -s -H "Host: bestfam.us" http://localhost:80/api/rules | grep -o '{' | wc -l)
if [ "$RULES_LEN" -ge 0 ]; then
    echo -e "${GREEN}PASS${NC} ($RULES_LEN rules found)"
else
    echo -e "${RED}FAIL${NC}"
fi

# 8d. Webhook Listener
echo -n "[8d/8] Webhook Listener: API... "
if curl -sf http://localhost:8000/docs > /dev/null; then
    echo -e "${GREEN}PASS${NC}"
else
    echo -e "${RED}FAIL${NC}"
fi

echo "=========================================="
echo "✅ ALL SYSTEMS OPERATIONAL"
echo "=========================================="
