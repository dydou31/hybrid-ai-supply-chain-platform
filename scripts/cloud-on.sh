#!/usr/bin/env bash
set -euo pipefail

# Exécution exclusivement via cloud-control.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -z "${HYBRID_AI_CLOUD_SUPERVISED:-}" ]]; then
  echo "❌ Utilise cloud-control.sh on|off" >&2
  exit 1
fi

# Signaler toute interruption ou erreur pendant une transition
cloud_error_handler() {
  local status=$?

  trap - EXIT

  if [[ "$status" -ne 0 ]]; then
    echo "❌ Opération CLOUD interrompue ou échouée (code $status)." >&2
    echo "⚠️ Vérifier l'état AWS avant toute nouvelle opération." >&2
    echo "⚠️ Le mode TRANSITION ne doit pas être remplacé automatiquement." >&2
  fi
}

trap cloud_error_handler EXIT

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

REGION="eu-west-3"
CLUSTER="hybrid-ai-cluster"
API="hybrid-ai-api-service"
GRAFANA="hybrid-ai-grafana-service"

echo "Démarrage du cloud AWS..."

echo "===== RESTAURATION INFRASTRUCTURE TERRAFORM ====="

TERRAFORM_DIR="$PROJECT_ROOT/terraform/aws"



terraform -chdir="$TERRAFORM_DIR" plan \
  -var="cloud_enabled=true" \
  -var="cloud_detach_only=false" \
  -out=cloud-on.tfplan

echo
echo "===== PLAN TERRAFORM CLOUD ON ====="
terraform -chdir="$TERRAFORM_DIR" show cloud-on.tfplan

echo
python3 "$PROJECT_ROOT/scripts/check-terraform-plan.py" "$PROJECT_ROOT/terraform/aws/cloud-on.tfplan"

if [[ "${HYBRID_AI_CLOUD_CONTROL_CENTER:-0}" != "1" ]]; then
  read -r -p "Appliquer ce plan AWS ? (oui/non) : " CONFIRMATION

  if [[ "$CONFIRMATION" != "oui" ]]; then
    echo "Opération annulée. Aucune modification Terraform appliquée."
    exit 1
  fi
else
  echo "Mode Control Center : validation Terraform réussie."
fi

# Bloquer tout arrêt automatique de RDS pendant CLOUD ON
aws ssm put-parameter \
  --name "/hybrid-ai/cloud/mode" \
  --value "TRANSITION" \
  --type "String" \
  --overwrite \
  --region "$REGION" >/dev/null

echo "Mode AWS : TRANSITION"


terraform -chdir="$TERRAFORM_DIR" apply cloud-on.tfplan

echo "✅ Infrastructure Terraform restaurée."


# Démarrer PostgreSQL avant les services ECS
RDS_STATUS=$(aws rds describe-db-instances \
  --db-instance-identifier hybrid-ai-postgres \
  --region "$REGION" \
  --query 'DBInstances[0].DBInstanceStatus' \
  --output text)

echo "État PostgreSQL : $RDS_STATUS"

if [ "$RDS_STATUS" = "stopped" ]; then
  aws rds start-db-instance \
    --db-instance-identifier hybrid-ai-postgres \
    --region "$REGION" >/dev/null
elif [ "$RDS_STATUS" != "available" ] && [ "$RDS_STATUS" != "starting" ]; then
  echo "État RDS incompatible avec le démarrage : $RDS_STATUS"
  exit 1
fi

echo "Attente de PostgreSQL..."
aws rds wait db-instance-available \
  --db-instance-identifier hybrid-ai-postgres \
  --region "$REGION"

echo "PostgreSQL disponible."


echo "Actualisation de REDIS_URL dans la Task Definition FastAPI..."

API_TASK_DEFINITION=$(python3 "$PROJECT_ROOT/scripts/update-ecs-redis-task.py")

if [[ -z "$API_TASK_DEFINITION" || "$API_TASK_DEFINITION" != arn:aws:ecs:* ]]; then
  echo "❌ Task Definition FastAPI invalide." >&2
  exit 1
fi

echo "Task Definition FastAPI : $API_TASK_DEFINITION"

aws ecs update-service \
  --cluster "$CLUSTER" \
  --service "$API" \
  --task-definition "$API_TASK_DEFINITION" \
  --desired-count 2 \
  --region "$REGION" \
  --query 'service.{Service:serviceName,Desired:desiredCount}' \
  --output table

aws ecs update-service \
  --cluster "$CLUSTER" \
  --service "$GRAFANA" \
  --desired-count 1 \
  --region "$REGION" \
  --query 'service.{Service:serviceName,Desired:desiredCount}' \
  --output table

echo "Attente de stabilisation des services ECS..."

aws ecs wait services-stable \
  --cluster "$CLUSTER" \
  --services "$API" "$GRAFANA" \
  --region "$REGION"

echo "✅ Services ECS stabilisés."

echo "Réactivation de l’Auto Scaling..."

aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id "service/$CLUSTER/$API" \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 4 \
  --suspended-state DynamicScalingInSuspended=false,DynamicScalingOutSuspended=false,ScheduledScalingSuspended=false \
  --region "$REGION"
# Confirmer le mode ON uniquement après un démarrage réussi
aws ssm put-parameter \
  --name "/hybrid-ai/cloud/mode" \
  --value "ON" \
  --type "String" \
  --overwrite \
  --region "$REGION" >/dev/null

echo "Mode AWS : ON"
echo "✅ CLOUD ON terminé."
