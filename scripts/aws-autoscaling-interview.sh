#!/bin/bash

set -e

CLUSTER="hybrid-ai-cluster"
SERVICE="hybrid-ai-api-service"
REGION="eu-west-3"
PROFILE="hybrid-ai-terraform"

echo "=================================================="
echo "     HYBRID AI PLATFORM - INTERVIEW DEMO"
echo "=================================================="
echo
echo "Production Auto Scaling"
echo "CPU target : 60%"
echo "Min tasks  : 2"
echo "Max tasks  : 4"
echo
echo "NOTE: Fast interview mode"
echo "The capacity change is triggered manually to avoid"
echo "waiting for the CloudWatch evaluation window."
echo

echo "Current ECS capacity:"
aws ecs describe-services \
  --cluster "$CLUSTER" \
  --services "$SERVICE" \
  --profile "$PROFILE" \
  --region "$REGION" \
  --query 'services[0].{Desired:desiredCount,Running:runningCount,Pending:pendingCount}' \
  --output table

echo
echo "Triggering capacity increase: 2 -> 4..."

aws ecs update-service \
  --cluster "$CLUSTER" \
  --service "$SERVICE" \
  --desired-count 4 \
  --profile "$PROFILE" \
  --region "$REGION" \
  >/dev/null

echo
echo "Capacity increase requested."
echo
echo "Auto Scaling architecture remains configured:"
echo "CloudWatch CPU -> Application Auto Scaling -> ECS Fargate"
echo
echo "Watch the monitoring terminal."
