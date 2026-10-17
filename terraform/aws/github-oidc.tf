data "aws_partition" "current" {}

resource "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list = [
    "sts.amazonaws.com"
  ]

  tags = {
    Name = "hybrid-ai-github-oidc"
  }
}

data "aws_iam_policy_document" "github_assume_role" {
  statement {
    effect = "Allow"

    actions = [
      "sts:AssumeRoleWithWebIdentity"
    ]

    principals {
      type = "Federated"

      identifiers = [
        aws_iam_openid_connect_provider.github.arn
      ]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"

      values = [
        "sts.amazonaws.com"
      ]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"

      values = [
        "repo:dydou31/hybrid-ai-supply-chain-platform:environment:production"
      ]
    }
  }
}

resource "aws_iam_role" "github_deploy" {
  name = "hybrid-ai-github-deploy"

  assume_role_policy = data.aws_iam_policy_document.github_assume_role.json
}

data "aws_iam_policy_document" "github_deploy" {
  statement {
    sid = "ECRLogin"

    effect = "Allow"

    actions = [
      "ecr:GetAuthorizationToken"
    ]

    resources = ["*"]
  }

  statement {
    sid = "ECRPublish"

    effect = "Allow"

    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:CompleteLayerUpload",
      "ecr:InitiateLayerUpload",
      "ecr:PutImage",
      "ecr:UploadLayerPart"
    ]

    resources = [
      aws_ecr_repository.api.arn
    ]
  }

  statement {
    sid    = "ECSServiceDeployment"
    effect = "Allow"

    actions = [
      "ecs:DescribeServices",
      "ecs:UpdateService"
    ]

    resources = [
      "arn:${data.aws_partition.current.partition}:ecs:eu-west-3:021914193620:service/hybrid-ai-cluster/hybrid-ai-api-service"
    ]
  }

  statement {
    sid    = "ECSTaskDefinitionRead"
    effect = "Allow"

    actions = [
      "ecs:DescribeTaskDefinition"
    ]

    resources = ["*"]
  }

  statement {
    sid    = "ECSTaskDefinitionRegister"
    effect = "Allow"

    actions = [
      "ecs:RegisterTaskDefinition"
    ]

    resources = [
      "arn:${data.aws_partition.current.partition}:ecs:eu-west-3:021914193620:task-definition/hybrid-ai-api:*"
    ]
  }

  statement {
    sid    = "CloudDeploymentLock"
    effect = "Allow"

    actions = [
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:DeleteItem"
    ]

    resources = [
      "arn:${data.aws_partition.current.partition}:dynamodb:eu-west-3:021914193620:table/hybrid-ai-cloud-lock"
    ]
  }

  statement {
    sid = "ReadCloudMode"

    effect = "Allow"

    actions = [
      "ssm:GetParameter"
    ]

    resources = [
      "arn:${data.aws_partition.current.partition}:ssm:eu-west-3:021914193620:parameter/hybrid-ai/cloud/mode"
    ]
  }

  statement {
    sid = "PassECSTaskRoles"

    effect = "Allow"

    actions = [
      "iam:PassRole"
    ]

    resources = [
      aws_iam_role.ecs_task_execution.arn,
      aws_iam_role.ecs_task.arn
    ]

    condition {
      test     = "StringEquals"
      variable = "iam:PassedToService"

      values = [
        "ecs-tasks.amazonaws.com"
      ]
    }
  }
}

resource "aws_iam_role_policy" "github_deploy" {
  name = "hybrid-ai-github-deploy-policy"
  role = aws_iam_role.github_deploy.id

  policy = data.aws_iam_policy_document.github_deploy.json
}

output "github_deploy_role_arn" {
  value = aws_iam_role.github_deploy.arn
}
