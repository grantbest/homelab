#!/bin/bash
# Basic Health Check
SERVICES=("traefik" "postgres" "redis" "temporal")
for svc in "${SERVICES[@]}"; do
    if docker ps --format "{{.Names}}" | grep -q "^$svc$"; then
        echo "✅ $svc is running"
    else
        echo "❌ $svc is missing"
    fi
done
