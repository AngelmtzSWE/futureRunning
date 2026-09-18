import argparse
from datetime import date
from pathlib import Path
from typing import Sequence

from .models import Goal, Run
from .services import current_streak, goal_progress, summarize
from .storage import RunStore


def _duration(value: str) -> int:
    parts = value.split(":")
    if len(parts) not in (2, 3):
        raise argparse.ArgumentTypeError("duration must be MM:SS or H:MM:SS")
    try:
        numbers = [int(part) for part in parts]
    except ValueError as error:
        raise argparse.ArgumentTypeError("duration must contain numbers") from error
    if any(number < 0 for number in numbers) or numbers[-1] >= 60 or (len(numbers) == 3 and numbers[1] >= 60):
        raise argparse.ArgumentTypeError("duration has invalid minute or second values")
    return numbers[0] * 60 + numbers[1] if len(numbers) == 2 else numbers[0] * 3600 + numbers[1] * 60 + numbers[2]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="futurerunning", description="A calm, data-driven running journal.")
    parser.add_argument("--data", type=Path, default=Path(".futurerunning/runs.json"), help="journal file location")
    subparsers = parser.add_subparsers(dest="command", required=True)
    add = subparsers.add_parser("add", help="log a completed run")
    add.add_argument("distance", type=float, help="distance in miles")
    add.add_argument("duration", type=_duration, help="duration as MM:SS or H:MM:SS")
    add.add_argument("--date", dest="run_date", default=date.today().isoformat())
    add.add_argument("--notes", default="")
    subparsers.add_parser("list", help="show recent runs")
    subparsers.add_parser("stats", help="show training totals and insights")
    goal = subparsers.add_parser("goal", help="set a mileage goal")
    goal.add_argument("miles", type=float)
    goal.add_argument("--start", default=date.today().replace(day=1).isoformat())
    goal.add_argument("--end", default=date.today().isoformat())
    return parser


def _header(title: str) -> None:
    print(f"\n{title}\n" + "-" * len(title))


def run_cli(arguments: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(arguments)
    store = RunStore(args.data)
    try:
        runs, goal = store.load()
        if args.command == "add":
            run = Run(args.distance, args.duration, args.run_date, args.notes)
            store.add(run)
            print(f"Logged {run.distance_miles:.2f} mi in {run.duration_display} ({run.pace_display}).")
        elif args.command == "list":
            _header("Recent runs")
            if not runs:
                print("No runs logged yet. Start with: futurerunning add 3.1 28:30")
            for run in sorted(runs, key=lambda item: item.run_date, reverse=True):
                note = f" | {run.notes}" if run.notes else ""
                print(f"{run.run_date}  {run.distance_miles:6.2f} mi  {run.duration_display:>12}  {run.pace_display}{note}")
        elif args.command == "stats":
            summary = summarize(runs)
            _header("Training snapshot")
            print(f"Runs logged       {summary.run_count}")
            print(f"Total distance    {summary.total_miles:.2f} mi")
            print(f"Total time        {summary.total_seconds // 3600}h {(summary.total_seconds % 3600) // 60:02d}m")
            print(f"Weighted pace     {summary.average_pace_display}")
            print(f"Longest run       {summary.longest_run_miles:.2f} mi")
            print(f"Current streak    {current_streak(runs)} day(s)")
            progress = goal_progress(runs, goal)
            if progress:
                completed, percentage, remaining = progress
                print(f"Goal progress     {completed:.2f}/{goal.target_miles:.2f} mi ({percentage:.0f}%, {remaining:.2f} remaining)")
        elif args.command == "goal":
            new_goal = Goal(args.miles, args.start, args.end)
            store.set_goal(new_goal)
            print(f"Goal set: {new_goal.target_miles:.2f} mi from {new_goal.start_date} to {new_goal.end_date}.")
        return 0
    except (ValueError, OSError) as error:
        print(f"Error: {error}")
        return 2
