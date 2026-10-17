
output "api_task_definition_arn" {
  description = "ARN de la Task Definition FastAPI gérée par Terraform"
  value       = aws_ecs_task_definition.api.arn
}
