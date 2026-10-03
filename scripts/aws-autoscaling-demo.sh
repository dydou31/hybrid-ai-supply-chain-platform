#!/bin/bash

set -e

CLUSTER="hybrid-ai-cluster"
SERVICE="hybrid-ai-api-service"
REGION="eu-west-3"
PROFILE="hybrid-ai-terraform"

RESOURCE_ID="service/$CLUSTER/$SERVICE"
POLICY_NAME="hybrid-ai-api-demo-scale-out"
ALARM_NAME="hybrid-ai-api-demo-cpu-high"

echo "=================================================="
echo "   HYBRID AI PLATFORM - FAST AUTOSCALING DEMO"
echo "=================================================="
echo
echo "Production policy : Target Tracking - CPU 60%"
echo "Demo policy       : Step Scaling - temporary"
echo "Demo alarm        : 1 x 60-second CPU period"
echo "Capacity          : min 2 | max 4"
echo

echo "[1/2] Creating temporary Step Scaling policy..."

POLICY_ARN=$(aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --resource-id "$RESOURCE_ID" \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-name "$POLICY_NAME" \
  --policy-type StepScaling \
  --step-scaling-policy-configuration '{
    "AdjustmentType": "ChangeInCapacity",
    "Cooldown": 30,
    "MetricAggregationType": "Average",
    "StepAdjustments": [
      {
        "MetricIntervalLowerBound": 0,
        "ScalingAdjustment": 2
      }
    ]
  }' \
  --profile "$PROFILE" \
  --region "$REGION" \
  --query 'PolicyARN' \
  --output text)

echo "[2/2] Creating temporary CloudWatch alarm..."

aws cloudwatch put-metric-alarm \
  --alarm-name "$ALARM_NAME" \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions \
    Name=ClusterName,Value="$CLUSTER" \
    Name=ServiceName,Value="$SERVICE" \
  --statistic Average \
  --period 60 \
  --evaluation-periods 1 \
  --datapoints-to-alarm 1 \
  --threshold 2 \
  --comparison-operator GreaterThanThreshold \
  --treat-missing-data notBreaching \
  --alarm-actions "$POLICY_ARN" \
  --profile "$PROFILE" \
  --region "$REGION"

echo
echo "FAST DEMO MODE ACTIVE"
echo "--------------------------------------------------"
echo "Normal Target Tracking policy remains at 60%."
echo "Temporary demo alarm triggers above 2% CPU."
echo "Only ONE 60-second CloudWatch period is required."
echo
echo "Now generate load while watching:"
echo "  ./scripts/aws-autoscaling-monitor.sh"
echo
echo "After the demo, run:"
echo "  ./scripts/aws-autoscaling-restore.sh"
echo
