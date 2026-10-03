#!/bin/bash

CLUSTER="hybrid-ai-cluster"
SERVICE="hybrid-ai-api-service"
REGION="eu-west-3"
PROFILE="hybrid-ai-terraform"
TARGET_CPU="60"

while true; do
  clear

  echo "=================================================="
  echo "      HYBRID AI PLATFORM - AWS AUTOSCALING"
  echo "=================================================="
  echo
  echo "Time: $(date '+%H:%M:%S')"
  echo

  # ECS service status
  SERVICE_DATA=$(aws ecs describe-services \
    --cluster "$CLUSTER" \
    --services "$SERVICE" \
    --profile "$PROFILE" \
    --region "$REGION" \
    --query 'services[0].[desiredCount,runningCount,pendingCount]' \
    --output text 2>/dev/null)

  read -r DESIRED RUNNING PENDING <<< "$SERVICE_DATA"

  # Latest CloudWatch CPU datapoint
  START_TIME=$(date -u -v-10M '+%Y-%m-%dT%H:%M:%SZ')
  END_TIME=$(date -u '+%Y-%m-%dT%H:%M:%SZ')

  CPU=$(aws cloudwatch get-metric-statistics \
    --namespace AWS/ECS \
    --metric-name CPUUtilization \
    --dimensions \
      Name=ClusterName,Value="$CLUSTER" \
      Name=ServiceName,Value="$SERVICE" \
    --statistics Average \
    --period 60 \
    --start-time "$START_TIME" \
    --end-time "$END_TIME" \
    --profile "$PROFILE" \
    --region "$REGION" \
    --query 'sort_by(Datapoints,&Timestamp)[-1].Average' \
    --output text 2>/dev/null)

  if [[ "$CPU" == "None" || -z "$CPU" ]]; then
    CPU_DISPLAY="Waiting for CloudWatch..."
  else
    CPU_DISPLAY=$(echo "$CPU" | LC_ALL=C awk '{printf "%.2f %%", $1}')
  fi

  # Human-readable status
  if [[ "$PENDING" -gt 0 ]]; then
    STATUS="SCALING IN PROGRESS"
  elif [[ "$DESIRED" -gt 2 ]]; then
    STATUS="SCALED OUT"
  elif [[ "$DESIRED" -eq 2 && "$RUNNING" -eq 2 ]]; then
    STATUS="STABLE"
  else
    STATUS="TRANSITION"
  fi

  echo "CPU Average : $CPU_DISPLAY"
  echo "CPU Target  : ${TARGET_CPU} %"
  echo
  echo "Desired     : $DESIRED"
  echo "Running     : $RUNNING"
  echo "Pending     : $PENDING"
  echo
  echo "Status      : $STATUS"
  echo
  echo "--------------------------------------------------"
  echo "Auto Scaling: min 2 | max 4 | target CPU ${TARGET_CPU}%"
  echo "CloudWatch CPU uses 60-second datapoints."
  echo
  echo "Refreshing every 5 seconds..."
  echo "Ctrl+C to stop"

  sleep 5
done
