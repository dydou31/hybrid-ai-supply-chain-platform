#!/usr/bin/env bash
set -Eeuo pipefail

: "${ECS_CLUSTER:?ECS_CLUSTER manquant}"
: "${ECS_SERVICE:?ECS_SERVICE manquant}"
: "${CONTAINER_NAME:?CONTAINER_NAME manquant}"
: "${CLOUD_MODE_PARAMETER:?CLOUD_MODE_PARAMETER manquant}"
: "${IMAGE_URI:?IMAGE_URI manquant}"

check_cloud_on() {
  local mode

  mode=$(aws ssm get-parameter \
    --name "$CLOUD_MODE_PARAMETER" \
    --query 'Parameter.Value' \
    --output text)

  if [[ "$mode" != "ON" ]]; then
    echo "::error::CLOUD=$mode. Déploiement interdit."
    exit 1
  fi
}

echo "🔒 Déploiement ECS sous verrou DynamoDB"

# 1. Vérifier le mode CLOUD
check_cloud_on

# 2. Récupérer la Task Definition réellement utilisée
TASK_DEFINITION=$(aws ecs describe-services \
  --cluster "$ECS_CLUSTER" \
  --services "$ECS_SERVICE" \
  --query 'services[0].taskDefinition' \
  --output text)

if [[ -z "$TASK_DEFINITION" || "$TASK_DEFINITION" == "None" ]]; then
  echo "::error::Task Definition introuvable."
  exit 1
fi

echo "Task Definition actuelle : $TASK_DEFINITION"

# 3. Récupérer sa configuration complète
aws ecs describe-task-definition \
  --task-definition "$TASK_DEFINITION" \
  --query 'taskDefinition' \
  --output json > task-definition-current.json

# 4. Modifier uniquement l'image FastAPI
jq --arg IMAGE "$IMAGE_URI" \
   --arg CONTAINER "$CONTAINER_NAME" '
  del(
    .taskDefinitionArn,
    .revision,
    .status,
    .requiresAttributes,
    .compatibilities,
    .registeredAt,
    .registeredBy,
    .deregisteredAt
  )
  | .containerDefinitions |= map(
      if .name == $CONTAINER
      then .image = $IMAGE
      else .
      end
    )
' task-definition-current.json > task-definition-new.json

MATCHES=$(jq --arg NAME "$CONTAINER_NAME" \
  '[.containerDefinitions[] | select(.name == $NAME)] | length' \
  task-definition-new.json)

if [[ "$MATCHES" != "1" ]]; then
  echo "::error::Conteneur FastAPI introuvable ou ambigu."
  exit 1
fi

# 5. Revérifier le mode CLOUD avant toute modification ECS
check_cloud_on

# 6. Enregistrer une nouvelle révision
NEW_TASK=$(aws ecs register-task-definition \
  --cli-input-json file://task-definition-new.json \
  --query 'taskDefinition.taskDefinitionArn' \
  --output text)

echo "✅ Nouvelle Task Definition : $NEW_TASK"

# 7. Déployer progressivement
check_cloud_on

aws ecs update-service \
  --cluster "$ECS_CLUSTER" \
  --service "$ECS_SERVICE" \
  --task-definition "$NEW_TASK" \
  --query 'service.{Name:serviceName,TaskDefinition:taskDefinition}' \
  --output json

# 8. Conserver le verrou jusqu'à la stabilisation
echo "⏳ Attente de stabilisation ECS (maximum 25 minutes)..."

STABLE=false

for attempt in $(seq 1 100); do
  SERVICE_JSON=$(aws ecs describe-services \
    --cluster "$ECS_CLUSTER" \
    --services "$ECS_SERVICE" \
    --output json)

  if [[ "$(jq '.services | length' <<< "$SERVICE_JSON")" != "1" ]]; then
    echo "::error::Service ECS introuvable."
    exit 1
  fi

  ROLLOUT_STATE=$(jq -r --arg TASK "$NEW_TASK" '
    [.services[0].deployments[]
     | select(.taskDefinition == $TASK)
     | .rolloutState // "UNKNOWN"] | first // "UNKNOWN"
  ' <<< "$SERVICE_JSON")

  RUNNING=$(jq -r '.services[0].runningCount' <<< "$SERVICE_JSON")
  DESIRED=$(jq -r '.services[0].desiredCount' <<< "$SERVICE_JSON")
  PENDING=$(jq -r '.services[0].pendingCount' <<< "$SERVICE_JSON")
  DEPLOYMENTS=$(jq -r '.services[0].deployments | length' <<< "$SERVICE_JSON")
  ACTIVE_TASK=$(jq -r '.services[0].taskDefinition' <<< "$SERVICE_JSON")

  echo "[$attempt/100] ECS : $RUNNING/$DESIRED running, $PENDING pending, rollout=$ROLLOUT_STATE"

  if [[ "$ROLLOUT_STATE" == "FAILED" ]]; then
    echo "::error::Le déploiement ECS a échoué."
    exit 1
  fi

  if [[ "$ROLLOUT_STATE" == "COMPLETED" &&
        "$RUNNING" == "$DESIRED" &&
        "$PENDING" == "0" &&
        "$DEPLOYMENTS" == "1" &&
        "$ACTIVE_TASK" == "$NEW_TASK" ]]; then
    STABLE=true
    break
  fi

  sleep 15
done

if [[ "$STABLE" != "true" ]]; then
  echo "::error::ECS non stabilisé après 25 minutes."
  exit 1
fi

echo "✅ Nouvelle version ECS stabilisée."

# 9. Vérifier la version réellement active
CURRENT_TASK=$(aws ecs describe-services \
  --cluster "$ECS_CLUSTER" \
  --services "$ECS_SERVICE" \
  --query 'services[0].taskDefinition' \
  --output text)

if [[ "$CURRENT_TASK" != "$NEW_TASK" ]]; then
  echo "::error::La Task Definition active ne correspond pas à la version déployée."
  exit 1
fi

echo "✅ Déploiement ECS terminé : $CURRENT_TASK"
