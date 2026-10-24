import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/check-terraform-plan.py"


def validate(monkeypatch, plan):
    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 0, json.dumps(plan), "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "fake.tfplan"])

    import runpy

    runpy.run_path(str(SCRIPT), run_name="__main__")


def test_plan_without_changes_is_allowed(monkeypatch):
    validate(monkeypatch, {"resource_changes": []})


def test_unauthorized_resource_is_refused(monkeypatch):
    import pytest

    with pytest.raises(SystemExit) as error:
        validate(monkeypatch, {
            "resource_changes": [{
                "address": "aws_db_instance.postgres",
                "change": {"actions": ["delete"]},
            }]
        })

    assert error.value.code == 1


def test_unexpected_autoscaling_change_is_refused(monkeypatch):
    import pytest

    with pytest.raises(SystemExit) as error:
        validate(monkeypatch, {
            "resource_changes": [{
                "address": "aws_appautoscaling_target.ecs_api",
                "change": {
                    "actions": ["update"],
                    "before": {"min_capacity": 0, "max_capacity": 4},
                    "after": {"min_capacity": 2, "max_capacity": 10},
                },
            }]
        })

    assert error.value.code == 1


def test_unexpected_ecs_task_definition_change_is_refused(monkeypatch):
    import pytest

    with pytest.raises(SystemExit) as error:
        validate(monkeypatch, {
            "resource_changes": [{
                "address": "aws_ecs_service.api",
                "change": {
                    "actions": ["update"],
                    "before": {"task_definition": "api:12"},
                    "after": {"task_definition": "api:99"},
                },
            }]
        })

    assert error.value.code == 1
