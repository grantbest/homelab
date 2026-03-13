variable "cloudflare_api_token" {
  description = "Cloudflare API Token with Zone:Edit, DNS:Edit, and Cloudflare Tunnel:Edit permissions"
  type        = string
  sensitive   = true
}

variable "cloudflare_account_id" {
  description = "Cloudflare Account ID"
  type        = string
}

variable "cloudflare_zone_id" {
  description = "Cloudflare Zone ID for bestfam.us"
  type        = string
}

variable "tunnel_name" {
  description = "Name of the Cloudflare Tunnel"
  type        = string
  default     = "homelab-tunnel"
}

variable "tunnel_secret" {
  description = "Secret for the Cloudflare Tunnel"
  type        = string
  sensitive   = true
}
