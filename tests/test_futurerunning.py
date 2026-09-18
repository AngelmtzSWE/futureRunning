import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from futurerunning.models import Goal, Run
from futurerunning.services import goal_progress, summarize
from futurerunning.storage import RunStore


class RunModelTests(unittest.TestCase):
    def test_run_calculates_pace_and_duration(self):
        run = Run(3.1, 28 * 60 + 30, "2026-09-17")
        self.assertEqual(run.pace_display, "9:12 /mi")
        self.assertEqual(run.duration_display, "28m 30s")

    def test_future_dates_are_rejected(self):
        with self.assertRaises(ValueError):
            Run(3, 1800, (date.today() + timedelta(days=1)).isoformat())


class StorageAndAnalyticsTests(unittest.TestCase):
    def test_store_round_trips_runs_and_goal(self):
        with tempfile.TemporaryDirectory() as directory:
            store = RunStore(Path(directory) / "runs.json")
            run = Run(5, 2700, "2026-09-01")
            goal = Goal(20, "2026-09-01", "2026-09-30")
            store.save([run], goal)
            runs, loaded_goal = store.load()
            self.assertEqual(runs[0].to_dict(), run.to_dict())
            self.assertEqual(loaded_goal.to_dict(), goal.to_dict())

    def test_summary_uses_weighted_average_pace(self):
        runs = [Run(2, 1200, "2026-09-01"), Run(4, 2400, "2026-09-02")]
        summary = summarize(runs)
        self.assertEqual(summary.total_miles, 6)
        self.assertEqual(summary.average_pace_seconds, 600)

    def test_goal_progress_only_counts_runs_in_period(self):
        goal = Goal(10, "2026-09-01", "2026-09-30")
        runs = [Run(4, 2400, "2026-09-10"), Run(3, 1800, "2026-08-31")]
        self.assertEqual(goal_progress(runs, goal), (4, 40.0, 6))


if __name__ == "__main__":
    unittest.main()
