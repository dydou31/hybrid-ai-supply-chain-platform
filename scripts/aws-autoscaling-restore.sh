#!/bin/bash

set -e

CLUSTER="hybrid-ai-cluster"
SERVICE="hybrid-ai-api-service"
REGION="eu-west-3"
PROFILE="hybrid-ai-terraform"

RESOURCE_ID="service/$CLUSTER/$SERVICE"

NORMAL_POLICY="hybrid-ai-api-cpu-autoscaling"
DEMO_POLICY="hybrid-ai-api-demo-scale-out"
DEMO_ALARM="hybrid-ai-api-demo-cpu-high"

echo "=================================================="
echo "   HYBRID AI PLATFORM - RESTORE NORMAL MODE"
echo "=================================================="
echo

echo "[1/4] Deleting temporary demo alarm..."

aws cloudwatch delete-alarms \
  --alarm-names "$DEMO_ALARM" \
  --profile "$PROFILE" \
  --region "$REGION"

echo "[2/4] Deleting temporary demo scaling policy..."

aws application-autoscaling delete-scaling-policy \
  --service-namespace ecs \
  --resource-id "$RESOURCE_ID" \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-name "$DEMO_POLICY" \
  --profile "$PROFILE" \
  --region "$REGION" 2>/dev/null || true

echo "[3/4] Ensuring normal Target Tracking policy is at 60%..."

aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --resource-id "$RESOURCE_ID" \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-name "$NORMAL_POLICY" \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 60.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
    },
    "ScaleOutCooldown": 60,
    "ScaleInCooldown": 60
  }' \
  --profile "$PROFILE" \
  --region "$REGION" \
  >/dev/null

echo "[4/4] Restoring ECS desired count to 2..."

aws ecs update-service \
  --cluster "$CLUSTER" \
  --service "$SERVICE" \
  --desired-count 2 \
  --profile "$PROFILE" \
  --region "$REGION" \
  >/dev/null

echo
echo "=================================================="
echo "          NORMAL MODE RESTORED"
echo "=================================================="
echo
echo "Demo alarm  : removed"
echo "Demo policy : removed"
echo "CPU target  : 60%"
echo "Desired     : 2"
echo "Min / Max   : 2 / 4"
echo
