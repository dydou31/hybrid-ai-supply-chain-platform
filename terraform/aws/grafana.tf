# ==========================================
# Grafana - Cloud Observability
# ==========================================

resource "aws_cloudwatch_log_group" "grafana" {
  name              = "/ecs/hybrid-ai-grafana"
  retention_in_days = 7
}

resource "aws_security_group" "grafana" {
  name        = "hybrid-ai-grafana-sg"
  description = "Allow Grafana traffic only from ALB"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Grafana from ALB"
    from_port       = 3000
    to_port         = 3000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_lb_target_group" "grafana" {
  name        = "hybrid-ai-grafana-tg"
  port        = 3000
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = aws_vpc.main.id

  health_check {
    enabled             = true
    path                = "/grafana/api/health"
    protocol            = "HTTP"
    matcher             = "200"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }
}

resource "aws_lb_listener_rule" "grafana" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 50

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.grafana.arn
  }

  condition {
    path_pattern {
      values = [
        "/grafana",
        "/grafana/*"
      ]
    }
  }
}

resource "aws_iam_role_policy" "grafana_amp" {
  name = "hybrid-ai-grafana-amp-read"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Effect = "Allow"

        Action = [
          "aps:QueryMetrics",
          "aps:GetSeries",
          "aps:GetLabels",
          "aps:GetMetricMetadata"
        ]

        Resource = aws_prometheus_workspace.main.arn
      }
    ]
  })
}

resource "aws_ecs_task_definition" "grafana" {
  family                   = "hybrid-ai-grafana"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"

  execution_role_arn = aws_iam_role.ecs_task_execution.arn
  task_role_arn      = aws_iam_role.ecs_task.arn

  cpu    = "256"
  memory = "512"

  container_definitions = jsonencode([
    {
      name      = "hybrid-ai-grafana"
      image     = "021914193620.dkr.ecr.eu-west-3.amazonaws.com/hybrid-ai-grafana:latest"
      essential = true

      environment = [
        {
          name  = "GF_SERVER_ROOT_URL"
          value = "%(protocol)s://%(domain)s/grafana/"
        },
        {
          name  = "GF_SERVER_SERVE_FROM_SUB_PATH"
          value = "true"
        },
        {
          name  = "GF_AUTH_ANONYMOUS_ENABLED"
          value = "true"
        },
        {
          name  = "GF_AUTH_ANONYMOUS_ORG_ROLE"
          value = "Viewer"
        },
        {
          name  = "GF_USERS_ALLOW_SIGN_UP"
          value = "false"
        }
      ]

      portMappings = [
        {
          containerPort = 3000
          hostPort      = 3000
          protocol      = "tcp"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"

        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.grafana.name
          "awslogs-region"        = "eu-west-3"
          "awslogs-stream-prefix" = "ecs-grafana"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "grafana" {
  name            = "hybrid-ai-grafana-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.grafana.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets = [
      aws_subnet.public.id,
      aws_subnet.public_b.id
    ]

    security_groups  = [aws_security_group.grafana.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.grafana.arn
    container_name   = "hybrid-ai-grafana"
    container_port   = 3000
  }

  health_check_grace_period_seconds = 60

  depends_on = [
    aws_lb_listener_rule.grafana
  ]
}