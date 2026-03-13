resource "cloudflare_argo_tunnel" "homelab_tunnel" {
  account_id = var.cloudflare_account_id
  name       = var.tunnel_name
  secret     = var.tunnel_secret
}

resource "cloudflare_tunnel_config" "homelab_config" {
  account_id = var.cloudflare_account_id
  tunnel_id  = cloudflare_argo_tunnel.homelab_tunnel.id

  config {
    ingress_rule {
      hostname = "bestfam.us"
      service  = "http://traefik:80"
    }
    ingress_rule {
      hostname = "dev.bestfam.us"
      service  = "http://traefik:80"
    }
    ingress_rule {
      hostname = "traefik.bestfam.us"
      service  = "http://traefik:8080"
    }
    ingress_rule {
      hostname = "temporal.bestfam.us"
      service  = "http://temporal-ui:8080"
    }
    # Default rule: return 404
    ingress_rule {
      service = "http_status:404"
    }
  }
}
