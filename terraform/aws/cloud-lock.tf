# Verrou distribué CLOUD ON / CLOUD OFF / surveillance RDS
resource "aws_dynamodb_table" "cloud_lock" {
  name         = "hybrid-ai-cloud-lock"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  ttl {
    attribute_name = "ExpiresAt"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = false
  }

  tags = {
    Project = "hybrid-ai"
    Purpose = "cloud-coordination"
  }
}
