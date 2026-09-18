# futureRunning

futureRunning is a local-first running journal built around a simple idea: make progress visible without making the runner manage a spreadsheet. The main experience is a browser dashboard designed around the one action that matters most: logging a run.

## What it does

- Logs distance, duration, date, and optional notes.
- Calculates pace consistently from seconds and miles.
- Stores structured data in a readable JSON file.
- Shows recent runs, total distance, total time, weighted pace, longest run, and current streak.
- Tracks a date-bounded mileage goal.
- Validates impossible values before they reach storage.
- Writes through a temporary file before replacing the journal, reducing the chance of a half-written save.

## Quick start

Requires Python 3.10 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .

# Open the visual dashboard (browser in Codespaces, desktop window locally)
python futureRunning.py
```

In Codespaces, open the forwarded port `8000` when the terminal prints `http://localhost:8000`. In the browser app:

1. Start on **Log a run** and enter distance, time, and date.
2. Use **Overview** to see pace, distance, longest run, streak, and progress.
3. Use **History** to review or delete runs.
4. Use **Goals** only when you want to add a personal mileage target.

The journal is saved to `.futurerunning/runs.json` by default. Use `--data path/to/journal.json` with the CLI to choose another location. The command-line interface is still available for scripting:

```bash
futurerunning add 3.1 28:30 --notes "Easy neighborhood loop"
futurerunning list
futurerunning stats
futurerunning goal 40 --start 2026-09-01 --end 2026-09-30
```

The dashboard is the main experience: enter your name, add your own runs, set a personal mileage goal, review every saved run, and delete mistakes. Nothing is preloaded by the application; every number shown comes from your journal.

## Development

Run the test suite without installing dependencies:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

The code is deliberately dependency-free. `src/futurerunning/` separates domain models, persistence, analytics, and CLI presentation so each part can evolve independently.

