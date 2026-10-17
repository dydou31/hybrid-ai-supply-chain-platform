#!/usr/bin/env python3

import json
import os
import subprocess
import sys
import time
import tempfile
from pathlib import Path

REGION = "eu-west-3"
CLUSTER = "hybrid-ai-cluster"
SERVICE = "hybrid-ai-api-service"
VALKEY = "hybrid-ai-valkey"
EXPECTED_IMAGE = ":aws-rds-fix-v2-20261017"


def aws(*args, payload=None):
    command = [
        "aws",
        *args,
        "--region", REGION,
        "--profile", "hybrid-ai-terraform",
        "--output", "json",
        "--no-cli-pager",
    ]

    result = subprocess.run(
        command,
        input=json.dumps(payload) if payload is not None else None,
        capture_output=True,
        text=True,
        check=True,
    )

    return json.loads(result.stdout)


def main():
    # Récupérer l'adresse du nouveau Valkey.
    cache = None

    for attempt in range(60):
        cache = aws(
            "elasticache",
            "describe-replication-groups",
            "--replication-group-id", VALKEY,
        )["ReplicationGroups"][0]

        if cache["Status"] == "available":
            break

        print(
            f"Valkey : {cache['Status']} "
            f"(tentative {attempt + 1}/60)",
            file=sys.stderr,
        )

        time.sleep(15)
    else:
        raise RuntimeError(
            "Valkey indisponible après 15 minutes."
        )

    endpoint = cache["NodeGroups"][0]["PrimaryEndpoint"]["Address"]
    redis_url = f"rediss://{endpoint}:6379/0"

    # Conserver la Task Definition actuellement utilisée.
    service = aws(
        "ecs", "describe-services",
        "--cluster", CLUSTER,
        "--services", SERVICE,
    )["services"][0]

    current_arn = service["taskDefinition"]

    task = aws(
        "ecs", "describe-task-definition",
        "--task-definition", current_arn,
    )["taskDefinition"]

    containers = task["containerDefinitions"]

    api = next(
        c for c in containers
        if c["name"] == "hybrid-ai-api"
    )

    # Interdire le retour vers une ancienne image.
    if not api["image"].endswith(EXPECTED_IMAGE):
        raise RuntimeError(
            "Image FastAPI inattendue : mise à jour refusée."
        )

    environment = api.setdefault("environment", [])

    current = next(
        (v for v in environment if v["name"] == "REDIS_URL"),
        None,
    )

    if current and current["value"] == redis_url:
        print(current_arn)
        return

    if current:
        current["value"] = redis_url
    else:
        environment.append({
            "name": "REDIS_URL",
            "value": redis_url,
        })

    # Conserver uniquement les champs acceptés lors
    # de l'enregistrement d'une Task Definition.
    allowed = {
        "family",
        "taskRoleArn",
        "executionRoleArn",
        "networkMode",
        "containerDefinitions",
        "volumes",
        "placementConstraints",
        "requiresCompatibilities",
        "cpu",
        "memory",
        "pidMode",
        "ipcMode",
        "proxyConfiguration",
        "inferenceAccelerators",
        "ephemeralStorage",
        "runtimePlatform",
        "enableFaultInjection",
    }

    definition = {
        key: value
        for key, value in task.items()
        if key in allowed
    }

    # Fichier temporaire privé pour transmettre la définition à AWS CLI.
    with tempfile.TemporaryDirectory(prefix="hybrid-ai-ecs-") as tmp:
        payload_path = Path(tmp) / "task-definition.json"
        payload_path.write_text(json.dumps(definition))
        payload_path.chmod(0o600)

        registered = aws(
            "ecs",
            "register-task-definition",
            "--cli-input-json", f"file://{payload_path}",
        )

    new_arn = registered["taskDefinition"]["taskDefinitionArn"]

    # Seul l'ARN est envoyé sur stdout pour être
    # récupéré directement par cloud-on.sh.
    print(new_arn)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Erreur Task Definition : {exc}", file=sys.stderr)
        sys.exit(1)
