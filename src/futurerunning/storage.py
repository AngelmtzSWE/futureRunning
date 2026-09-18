import json
from pathlib import Path
from typing import Any

from .models import Goal, Run


class RunStore:
    """Persists the journal in one human-readable JSON document."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> tuple[list[Run], Goal | None]:
        if not self.path.exists():
            return [], None
        try:
            data: dict[str, Any] = json.loads(self.path.read_text())
            runs = [Run.from_dict(item) for item in data.get("runs", [])]
            goal_data = data.get("goal")
            return runs, Goal.from_dict(goal_data) if goal_data else None
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            raise ValueError(f"could not read journal at {self.path}: {error}") from error

    def save(self, runs: list[Run], goal: Goal | None = None) -> None:
        self.save_with_profile(runs, goal)

    def save_with_profile(self, runs: list[Run], goal: Goal | None = None, profile_name: str = "") -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        existing_name = ""
        if self.path.exists():
            try:
                existing_name = str(json.loads(self.path.read_text()).get("profile_name", ""))
            except json.JSONDecodeError:
                existing_name = ""
        payload = {
            "version": 1,
            "profile_name": profile_name or existing_name,
            "runs": [run.to_dict() for run in runs],
            "goal": goal.to_dict() if goal else None,
        }
        temporary_path = self.path.with_suffix(".tmp")
        temporary_path.write_text(json.dumps(payload, indent=2) + "\n")
        temporary_path.replace(self.path)

    def add(self, run: Run) -> None:
        runs, goal = self.load()
        self.save([*runs, run], goal)

    def set_goal(self, goal: Goal) -> None:
        runs, _ = self.load()
        self.save(runs, goal)

    def get_profile_name(self) -> str:
        if not self.path.exists():
            return ""
        try:
            return str(json.loads(self.path.read_text()).get("profile_name", ""))
        except (json.JSONDecodeError, OSError):
            return ""

    def set_profile_name(self, profile_name: str) -> None:
        runs, goal = self.load()
        self.save_with_profile(runs, goal, profile_name.strip())

    def delete(self, run_id: str) -> None:
        runs, goal = self.load()
        self.save([run for run in runs if run.id != run_id], goal)
