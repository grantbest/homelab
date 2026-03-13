resource "cloudflare_record" "root" {
  zone_id = var.cloudflare_zone_id
  name    = "@"
  value   = "${cloudflare_argo_tunnel.homelab_tunnel.id}.cfargotunnel.com"
  type    = "CNAME"
  proxied = true
}

resource "cloudflare_record" "dev" {
  zone_id = var.cloudflare_zone_id
  name    = "dev"
  value   = "${cloudflare_argo_tunnel.homelab_tunnel.id}.cfargotunnel.com"
  type    = "CNAME"
  proxied = true
}

resource "cloudflare_record" "traefik" {
  zone_id = var.cloudflare_zone_id
  name    = "traefik"
  value   = "${cloudflare_argo_tunnel.homelab_tunnel.id}.cfargotunnel.com"
  type    = "CNAME"
  proxied = true
}

resource "cloudflare_record" "temporal" {
  zone_id = var.cloudflare_zone_id
  name    = "temporal"
  value   = "${cloudflare_argo_tunnel.homelab_tunnel.id}.cfargotunnel.com"
  type    = "CNAME"
  proxied = true
}
