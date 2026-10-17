# Preserve the existing Valkey resource when introducing cloud_enabled.

moved {
  from = aws_elasticache_replication_group.valkey
  to   = aws_elasticache_replication_group.valkey[0]
}

# Preserve the existing ALB when introducing cloud_enabled.
moved {
  from = aws_lb.api
  to   = aws_lb.api[0]
}

# Preserve existing Target Groups when introducing cloud_enabled.
moved {
  from = aws_lb_target_group.api
  to   = aws_lb_target_group.api[0]
}

moved {
  from = aws_lb_target_group.grafana
  to   = aws_lb_target_group.grafana[0]
}

# Preserve existing listeners when introducing cloud_enabled.
moved {
  from = aws_lb_listener.http
  to   = aws_lb_listener.http[0]
}

moved {
  from = aws_lb_listener_rule.grafana
  to   = aws_lb_listener_rule.grafana[0]
}
