# ============================================================
# RDS GUARD — Surveillance automatique du mode CLOUD OFF
# ============================================================

data "archive_file" "rds_guard" {
  type        = "zip"
  source_file = "${path.module}/lambda/rds_guard.py"
  output_path = "${path.module}/lambda/rds_guard.zip"
}

resource "aws_iam_role" "rds_guard" {
  name = "hybrid-ai-rds-guard-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "rds_guard" {
  name = "hybrid-ai-rds-guard-policy"
  role = aws_iam_role.rds_guard.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter"
        ]
        Resource = "arn:aws:ssm:eu-west-3:021914193620:parameter/hybrid-ai/cloud/mode"
      },
      {
        Effect = "Allow"
        Action = [
          "ecs:DescribeServices"
        ]
        Resource = [
          "arn:aws:ecs:eu-west-3:021914193620:service/hybrid-ai-cluster/hybrid-ai-api-service",
          "arn:aws:ecs:eu-west-3:021914193620:service/hybrid-ai-cluster/hybrid-ai-grafana-service"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "rds:DescribeDBInstances"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "rds:StopDBInstance"
        ]
        Resource = "arn:aws:rds:eu-west-3:021914193620:db:hybrid-ai-postgres"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem"
        ]
        Resource = aws_dynamodb_table.cloud_lock.arn
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:eu-west-3:021914193620:log-group:/aws/lambda/hybrid-ai-rds-guard:*"
      }
    ]
  })
}

resource "aws_cloudwatch_log_group" "rds_guard" {
  name              = "/aws/lambda/hybrid-ai-rds-guard"
  retention_in_days = 7
}

resource "aws_lambda_function" "rds_guard" {
  function_name = "hybrid-ai-rds-guard"

  role    = aws_iam_role.rds_guard.arn
  handler = "rds_guard.lambda_handler"
  runtime = "python3.12"

  filename         = data.archive_file.rds_guard.output_path
  source_code_hash = data.archive_file.rds_guard.output_base64sha256

  timeout     = 30
  memory_size = 128

  environment {
    variables = {
      DRY_RUN = "false"
    }
  }

  depends_on = [
    aws_iam_role_policy.rds_guard,
    aws_cloudwatch_log_group.rds_guard
  ]
}

# Planification quotidienne désactivée pendant les tests.
resource "aws_cloudwatch_event_rule" "rds_guard" {
  name                = "hybrid-ai-rds-guard-daily"
  description         = "Check RDS state when Hybrid AI Cloud is OFF"
  schedule_expression = "rate(1 day)"
  state               = "ENABLED"
}

resource "aws_cloudwatch_event_target" "rds_guard" {
  rule = aws_cloudwatch_event_rule.rds_guard.name
  arn  = aws_lambda_function.rds_guard.arn
}

resource "aws_lambda_permission" "rds_guard_eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.rds_guard.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.rds_guard.arn
}
