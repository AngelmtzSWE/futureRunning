from datetime import date

from .models import Goal, Run, Summary


def summarize(runs: list[Run]) -> Summary:
    if not runs:
        return Summary(0, 0.0, 0, None, 0.0)
    total_miles = sum(run.distance_miles for run in runs)
    total_seconds = sum(run.duration_seconds for run in runs)
    return Summary(len(runs), total_miles, total_seconds, total_seconds / total_miles, max(run.distance_miles for run in runs))


def runs_in_goal_period(runs: list[Run], goal: Goal) -> list[Run]:
    return [run for run in runs if goal.start_date <= run.run_date <= goal.end_date]


def goal_progress(runs: list[Run], goal: Goal | None) -> tuple[float, float, float] | None:
    if goal is None:
        return None
    completed = sum(run.distance_miles for run in runs_in_goal_period(runs, goal))
    percentage = min(completed / goal.target_miles * 100, 100)
    return completed, percentage, round(max(goal.target_miles - completed, 0), 2)


def current_streak(runs: list[Run]) -> int:
    dates = {date.fromisoformat(run.run_date) for run in runs}
    streak = 0
    day = date.today()
    while day in dates:
        streak += 1
        day = day.fromordinal(day.toordinal() - 1)
    return streak
