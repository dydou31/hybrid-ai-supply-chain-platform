import json, sys

plan = json.load(sys.stdin)

allowed_deletions = {
    "aws_lb.api[0]",
    "aws_lb_listener.http[0]",
    "aws_lb_listener_rule.grafana[0]",
    "aws_lb_target_group.api[0]",
    "aws_lb_target_group.grafana[0]",
    "aws_elasticache_replication_group.valkey[0]",
}

allowed_updates = {
    "aws_cloudfront_distribution.frontend",
    "aws_ecs_service.api",
    "aws_ecs_service.grafana",
}

errors = []
deletions = []

for resource in plan.get("resource_changes", []):
    address = resource["address"]
    actions = resource["change"]["actions"]

    if actions == ["no-op"]:
        continue

    if address in allowed_deletions and actions == ["delete"]:
        deletions.append(address)
    elif address in allowed_updates and actions == ["update"]:
        allowed_attributes = {
            "aws_cloudfront_distribution.frontend": {
                "origin",
                "ordered_cache_behavior",
            },
            "aws_ecs_service.api": {"load_balancer"},
            "aws_ecs_service.grafana": {"load_balancer"},
        }

        before = resource["change"].get("before") or {}
        after = resource["change"].get("after") or {}

        changed = {
            key
            for key in set(before) | set(after)
            if before.get(key) != after.get(key)
        }

        unexpected = changed - allowed_attributes[address]

        if unexpected:
            errors.append((address, sorted(unexpected)))
        else:
            print(f"✅ Modification autorisée : {address} ({sorted(changed)})")
    else:
        errors.append((address, actions))

for address in deletions:
    print(f"✅ Suppression autorisée : {address}")

for address, actions in errors:
    print(f"⛔ Modification interdite : {address} ({actions})")

if errors:
    sys.exit(1)

print("✅ Plan CLOUD OFF validé.")
