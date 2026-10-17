#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

if len(sys.argv) != 2:
    sys.exit("Usage: check-terraform-plan.py <plan.tfplan>")

result = subprocess.run(
    ["terraform", "show", "-json", str(Path(sys.argv[1]).resolve())],
    cwd=Path(__file__).resolve().parent.parent / "terraform" / "aws",
    capture_output=True,
    text=True,
    check=True,
)

plan = json.loads(result.stdout)


# Modifications explicitement autorisées pour CLOUD ON.
ALLOWED = {
    "aws_appautoscaling_target.ecs_api": ["update"],
    "aws_cloudfront_distribution.frontend": ["update"],
    "aws_ecs_service.api": ["update"],
    "aws_ecs_service.grafana": ["update"],
    "aws_ecs_task_definition.api": ["delete", "create"],
    "aws_elasticache_replication_group.valkey[0]": ["create"],
    "aws_lb.api[0]": ["create"],
    "aws_lb_listener.http[0]": ["create"],
    "aws_lb_listener_rule.grafana[0]": ["create"],
    "aws_lb_target_group.api[0]": ["create"],
    "aws_lb_target_group.grafana[0]": ["create"],
}

dangerous = []

for resource in plan.get("resource_changes", []):
    address = resource["address"]
    actions = resource["change"]["actions"]

    if actions == ["no-op"]:
        continue

    if ALLOWED.get(address) != actions:
        dangerous.append(f"{address} : {actions}")
        continue

    if address == "aws_appautoscaling_target.ecs_api":
        change = resource["change"]
        before = change.get("before") or {}
        after = change.get("after") or {}

        changed = {
            key for key in set(before) | set(after)
            if before.get(key) != after.get(key)
        }

        if (
            changed != {"min_capacity"}
            or before.get("min_capacity") != 0
            or after.get("min_capacity") != 2
        ):
            dangerous.append(
                f"{address} : modification Auto Scaling inattendue"
            )

if dangerous:
    print("❌ PLAN REFUSÉ : modifications non autorisées !")
    for item in dangerous:
        print(" -", item)
    sys.exit(1)

print("✅ Plan CLOUD ON validé : actions conformes à la liste blanche.")
