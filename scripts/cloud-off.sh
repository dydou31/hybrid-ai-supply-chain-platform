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
TERRAFORM_DIR="$PROJECT_ROOT/terraform/aws"

REGION="eu-west-3"
CLUSTER="hybrid-ai-cluster"
API="hybrid-ai-api-service"
GRAFANA="hybrid-ai-grafana-service"

echo "===== CLOUD OFF : PRÉVALIDATION TERRAFORM ====="

terraform -chdir="$TERRAFORM_DIR" plan   -var="cloud_enabled=false"   -var="cloud_detach_only=false"   -out=cloud-off-precheck.tfplan

terraform -chdir="$TERRAFORM_DIR" show -json cloud-off-precheck.tfplan   | python3 "$SCRIPT_DIR/validate-cloud-off-plan.py"

echo "✅ Prévalidation Terraform réussie."

echo "Activation du mode CLOUD OFF..."

# Empêcher la surveillance automatique d'intervenir pendant CLOUD OFF
aws ssm put-parameter \
  --name "/hybrid-ai/cloud/mode" \
  --value "TRANSITION" \
  --type "String" \
  --overwrite \
  --region "$REGION" >/dev/null

echo "Mode AWS : TRANSITION"

# Suspendre l'autoscaling FastAPI
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id "service/$CLUSTER/$API" \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 0 \
  --max-capacity 4 \
  --suspended-state DynamicScalingInSuspended=true,DynamicScalingOutSuspended=true,ScheduledScalingSuspended=true \
  --region "$REGION"

# Arrêter FastAPI
aws ecs update-service \
  --cluster "$CLUSTER" \
  --service "$API" \
  --desired-count 0 \
  --region "$REGION" \
  --query 'service.{Service:serviceName,Desired:desiredCount}' \
  --output table

# Arrêter Grafana
aws ecs update-service \
  --cluster "$CLUSTER" \
  --service "$GRAFANA" \
  --desired-count 0 \
  --region "$REGION" \
  --query 'service.{Service:serviceName,Desired:desiredCount}' \
  --output table

echo "Arrêt ECS demandé."

echo "Attente de l'arrêt complet des services ECS..."

aws ecs wait services-stable \
  --cluster "$CLUSTER" \
  --services "$API" "$GRAFANA" \
  --region "$REGION"

echo "Services ECS stabilisés."

# Vérifier qu'aucune tâche ne fonctionne encore
RUNNING=$(aws ecs describe-services \
  --cluster "$CLUSTER" \
  --services "$API" "$GRAFANA" \
  --region "$REGION" \
  --query 'sum(services[].runningCount) == `0` && sum(services[].pendingCount) == `0`' \
  --output text)

if [ "$RUNNING" != "True" ]; then
  echo "Erreur : $RUNNING tâches ECS encore actives ou en attente."
  exit 1
fi

# Arrêter PostgreSQL
RDS_STATUS=$(aws rds describe-db-instances \
  --db-instance-identifier hybrid-ai-postgres \
  --region "$REGION" \
  --query 'DBInstances[0].DBInstanceStatus' \
  --output text)

echo "État PostgreSQL : $RDS_STATUS"

if [ "$RDS_STATUS" = "available" ]; then
  aws rds stop-db-instance \
    --db-instance-identifier hybrid-ai-postgres \
    --region "$REGION" >/dev/null

  echo "Arrêt PostgreSQL demandé."
elif [ "$RDS_STATUS" = "stopped" ]; then
  echo "PostgreSQL est déjà arrêté."
elif [ "$RDS_STATUS" = "stopping" ]; then
  echo "PostgreSQL est déjà en cours d'arrêt."
else
  echo "État RDS inattendu : $RDS_STATUS"
  exit 1
fi

echo "===== CLOUD OFF : PLAN TERRAFORM ====="

terraform -chdir="$TERRAFORM_DIR" plan \
  -var="cloud_enabled=false" \
  -var="cloud_detach_only=false" \
  -out=cloud-off-final.tfplan

terraform -chdir="$TERRAFORM_DIR" show cloud-off-final.tfplan

# Ne jamais créer de ressources pendant CLOUD OFF.
# Refuser toute modification non explicitement autorisée.
terraform -chdir="$TERRAFORM_DIR" show -json cloud-off-final.tfplan | python3 "$SCRIPT_DIR/validate-cloud-off-plan.py"

echo "✅ Vérification Terraform terminée."

# Appliquer uniquement le plan Terraform qui vient d'être validé.
echo "===== CLOUD OFF : APPLICATION TERRAFORM ====="
terraform -chdir="$TERRAFORM_DIR" apply -input=false cloud-off-final.tfplan
echo "✅ Plan Terraform CLOUD OFF appliqué."

echo "✅ Plan Terraform exécuté et validé."
echo
# Attendre l'arrêt effectif de PostgreSQL avant de déclarer OFF.
echo "Vérification de l'arrêt PostgreSQL..."

echo "Attente de PostgreSQL stopped..."

for attempt in $(seq 1 60); do
  RDS_STATUS=$(aws rds describe-db-instances \
    --db-instance-identifier hybrid-ai-postgres \
    --region "$REGION" \
    --query 'DBInstances[0].DBInstanceStatus' \
    --output text)

  if [[ "$RDS_STATUS" == "stopped" ]]; then
    break
  fi

  echo "RDS : $RDS_STATUS (tentative $attempt/60)"
  sleep 15
done

if [[ "$RDS_STATUS" != "stopped" ]]; then
  echo "⛔ Délai dépassé : PostgreSQL n'est pas arrêté."
  exit 1
fi

RDS_FINAL_STATUS=$(aws rds describe-db-instances \
  --db-instance-identifier hybrid-ai-postgres \
  --region "$REGION" \
  --query 'DBInstances[0].DBInstanceStatus' \
  --output text)

if [[ "$RDS_FINAL_STATUS" != "stopped" ]]; then
  echo "⛔ PostgreSQL n'est pas arrêté : $RDS_FINAL_STATUS"
  exit 1
fi

echo "✅ PostgreSQL arrêté."

# Confirmer le mode OFF après vérification des services

aws ssm put-parameter \
  --name "/hybrid-ai/cloud/mode" \
  --value "OFF" \
  --type "String" \
  --overwrite \
  --region "$REGION" >/dev/null

echo "Mode AWS : OFF"
echo "✅ CLOUD OFF terminé."
