variable "cloud_enabled" {
  description = "Enable or disable on-demand AWS resources (ALB, Valkey and related components)"
  type        = bool
  default     = true
}

variable "cloud_detach_only" {
  description = "Keep ALB and Valkey temporarily while detaching ECS services"
  type        = bool
  default     = false
}
