# Homelab Infrastructure: Cloudflare Edition

I have updated your homelab setup to use a **Cloudflare Tunnel**. This is the most secure way to host from home.

### How it Works:
- **Cloudflared Container**: Connects your MacBook to Cloudflare via an encrypted tunnel.
- **No Port Forwarding**: You do **not** need to open any ports on your eero router.
- **Traefik**: Receives traffic from the tunnel and routes it to your private services.

### How to Start:

1. **Start the Solution**:
   ```bash
   cd /Users/grantbest/Documents/homelab
   docker compose up -d
   ```

2. **Cloudflare Dashboard Configuration**:
   In your Cloudflare Zero Trust dashboard, under the tunnel you created:
   - Go to **Public Hostnames**.
   - **Add a public hostname**:
     - **Subdomain**: (leave blank for root)
     - **Domain**: `bestfam.us`
     - **Service Type**: `HTTP`
     - **URL**: `traefik:80`
   - **Add another public hostname** (optional for dashboard):
     - **Subdomain**: `traefik`
     - **Domain**: `bestfam.us`
     - **Service Type**: `HTTP`
     - **URL**: `traefik:80`

3. **Verify**:
   - Once the tunnel is "Active" in Cloudflare and the Docker container is running, visit `https://bestfam.us`.
   - You should see the `whoami` service response!

### Files Updated:
- `docker-compose.yml`: Added `cloudflared` service and simplified Traefik labels.
- `.env`: Added your specific tunnel token.
- `README.md`: New instructions for the Cloudflare-first approach.
