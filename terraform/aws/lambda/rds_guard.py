import os
import time
import uuid

import boto3
from botocore.exceptions import ClientError

REGION = os.environ.get("AWS_REGION", "eu-west-3")
RDS_ID = "hybrid-ai-postgres"
ECS_CLUSTER = "hybrid-ai-cluster"
ECS_SERVICES = [
    "hybrid-ai-api-service",
    "hybrid-ai-grafana-service",
]
LOCK_TABLE = "hybrid-ai-cloud-lock"
LOCK_ID = "cloud-operation"
MODE_PARAMETER = "/hybrid-ai/cloud/mode"
DRY_RUN = os.environ.get("DRY_RUN", "true").lower() != "false"

ssm = boto3.client("ssm", region_name=REGION)
ecs = boto3.client("ecs", region_name=REGION)
rds = boto3.client("rds", region_name=REGION)
dynamodb = boto3.client("dynamodb", region_name=REGION)


def lambda_handler(event, context):
    owner = str(uuid.uuid4())
    now = int(time.time())

    try:
        dynamodb.put_item(
            TableName=LOCK_TABLE,
            Item={
                "LockID": {"S": LOCK_ID},
                "Owner": {"S": owner},
                "ExpiresAt": {"N": str(now + 120)},
            },
            ConditionExpression=(
                "attribute_not_exists(LockID) OR ExpiresAt < :now"
            ),
            ExpressionAttributeValues={
                ":now": {"N": str(now)}
            },
        )
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return {"status": "SKIPPED", "reason": "Cloud lock busy"}
        raise

    try:
        mode = ssm.get_parameter(Name=MODE_PARAMETER)["Parameter"]["Value"]

        if mode != "OFF":
            return {"status": "SKIPPED", "reason": f"Cloud mode: {mode}"}

        response = ecs.describe_services(
            cluster=ECS_CLUSTER,
            services=ECS_SERVICES,
        )

        services = response.get("services", [])

        if response.get("failures") or len(services) != len(ECS_SERVICES):
            return {"status": "SKIPPED", "reason": "ECS services not found"}

        for service in services:
            if service.get("status") != "ACTIVE":
                return {"status": "SKIPPED", "reason": "ECS service not active"}

            if len(service.get("deployments", [])) != 1:
                return {"status": "SKIPPED", "reason": "ECS deployment in progress"}

            if (
                service.get("desiredCount", 0) != 0
                or service.get("runningCount", 0) != 0
                or service.get("pendingCount", 0) != 0
            ):
                return {
                    "status": "SKIPPED",
                    "reason": "ECS services are not fully stopped",
                }

        database = rds.describe_db_instances(
            DBInstanceIdentifier=RDS_ID
        )["DBInstances"][0]

        if database["DBInstanceStatus"] != "available":
            return {
                "status": "SKIPPED",
                "reason": f"RDS status: {database['DBInstanceStatus']}",
            }

        # Relecture du mode avant toute demande d'arrêt.
        current_mode = ssm.get_parameter(
            Name=MODE_PARAMETER
        )["Parameter"]["Value"]

        if current_mode != "OFF":
            return {"status": "SKIPPED", "reason": "Cloud mode changed"}

        if DRY_RUN:
            return {
                "status": "DRY_RUN",
                "action": "WOULD_STOP_RDS",
                "database": RDS_ID,
            }

        # Vérifier la propriété et renouveler le bail avant l'arrêt RDS.
        now = int(time.time())
        dynamodb.update_item(
            TableName=LOCK_TABLE,
            Key={"LockID": {"S": LOCK_ID}},
            UpdateExpression="SET ExpiresAt = :expires",
            ConditionExpression="#owner = :owner AND ExpiresAt > :now",
            ExpressionAttributeNames={"#owner": "Owner"},
            ExpressionAttributeValues={
                ":owner": {"S": owner},
                ":now": {"N": str(now)},
                ":expires": {"N": str(now + 120)},
            },
        )

        rds.stop_db_instance(DBInstanceIdentifier=RDS_ID)

        return {"status": "SUCCESS", "action": "RDS_STOP_REQUESTED"}

    finally:
        try:
            dynamodb.delete_item(
                TableName=LOCK_TABLE,
                Key={"LockID": {"S": LOCK_ID}},
                ConditionExpression="#owner = :owner",
                ExpressionAttributeNames={"#owner": "Owner"},
                ExpressionAttributeValues={
                    ":owner": {"S": owner}
                },
            )
        except ClientError as exc:
            if exc.response["Error"]["Code"] != "ConditionalCheckFailedException":
                raise
