#!/bin/bash

# App: Betting Engine
# Goal: Verify the Dashboard is reachable through Traefik locally

# Check if bestfam.us responds via Traefik on port 80
BODY=$(curl -s -H "Host: bestfam.us" http://localhost:80/)

if [[ "$BODY" == *"404 page not found"* ]]; then
    echo " (Reached Traefik but not the App) "
    exit 1
else
    # If the body is NOT Traefik's default, it means we reached the app container
    exit 0
fi
