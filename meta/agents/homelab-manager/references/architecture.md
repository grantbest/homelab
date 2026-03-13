# Homelab Architecture

## Core Components
- **Traefik (v3.1):** Edge router and SSL termination (Let\s Encrypt).
- **Postgres (v16):** Centralized database for all apps.
- **Redis (v7):** Centralized message broker/cache.
- **Temporal:** Workflow orchestration engine.
- **Cloudflared:** Secure tunnel for external access.

## Networking
- All services share the `homelab_global` bridge network.
- Internal service discovery uses container names.
