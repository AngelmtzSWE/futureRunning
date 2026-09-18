import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .models import Goal, Run
from .services import current_streak, goal_progress, summarize
from .storage import RunStore

STATIC_DIR = Path(__file__).parent / "static"


def _duration(value: str) -> int:
    parts = [int(part) for part in value.split(":")]
    if len(parts) == 2:
        minutes, seconds = parts
        if seconds >= 60:
            raise ValueError("seconds must be below 60")
        return minutes * 60 + seconds
    if len(parts) == 3:
        hours, minutes, seconds = parts
        if minutes >= 60 or seconds >= 60:
            raise ValueError("minutes and seconds must be below 60")
        return hours * 3600 + minutes * 60 + seconds
    raise ValueError("time must be MM:SS or H:MM:SS")


def _state(store: RunStore) -> dict:
    runs, goal = store.load()
    summary = summarize(runs)
    progress = goal_progress(runs, goal)
    return {
        "profile_name": store.get_profile_name(),
        "runs": [{**run.to_dict(), "pace_seconds_per_mile": run.pace_seconds_per_mile} for run in sorted(runs, key=lambda item: item.run_date, reverse=True)],
        "summary": {
            "run_count": summary.run_count,
            "total_miles": summary.total_miles,
            "total_seconds": summary.total_seconds,
            "average_pace_seconds": summary.average_pace_seconds,
            "longest_run_miles": summary.longest_run_miles,
        },
        "streak": current_streak(runs),
        "goal": goal.to_dict() if goal else None,
        "goal_progress": {"completed": progress[0], "percentage": progress[1]} if progress else None,
    }


def create_server(host: str = "0.0.0.0", port: int = 8000, data_path: Path | None = None) -> ThreadingHTTPServer:
    store = RunStore(data_path or Path(".futurerunning/runs.json"))

    class Handler(BaseHTTPRequestHandler):
        def send_bytes(self, body: bytes, content_type: str, status: int = 200) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def send_json(self, payload: object, status: int = 200) -> None:
            self.send_bytes(json.dumps(payload).encode(), "application/json", status)

        def read_json(self) -> dict:
            length = int(self.headers.get("Content-Length", 0))
            return json.loads(self.rfile.read(length))

        def do_GET(self) -> None:
            if self.path == "/":
                self.send_bytes((STATIC_DIR / "index.html").read_bytes(), "text/html; charset=utf-8")
                return
            if self.path == "/static/style.css":
                self.send_bytes((STATIC_DIR / "style.css").read_bytes(), "text/css; charset=utf-8")
                return
            if self.path == "/static/app.js":
                self.send_bytes((STATIC_DIR / "app.js").read_bytes(), "text/javascript; charset=utf-8")
                return
            if self.path == "/api/state":
                self.send_json(_state(store))
                return
            self.send_error(404)

        def do_POST(self) -> None:
            try:
                data = self.read_json()
                if self.path == "/api/runs":
                    store.add(Run(float(data["distance"]), _duration(str(data["duration"])), str(data["run_date"]), str(data.get("notes", ""))))
                elif self.path == "/api/profile":
                    store.set_profile_name(str(data.get("name", "")))
                elif self.path == "/api/goal":
                    store.set_goal(Goal(float(data["miles"]), str(data["start"]), str(data["end"])))
                else:
                    self.send_error(404)
                    return
                self.send_json({"ok": True})
            except (ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
                self.send_json({"error": str(error)}, 400)

        def do_DELETE(self) -> None:
            if self.path.startswith("/api/runs/"):
                store.delete(self.path.rsplit("/", 1)[-1])
                self.send_json({"ok": True})
                return
            self.send_error(404)

        def log_message(self, *_args) -> None:
            return

    return ThreadingHTTPServer((host, port), Handler)


def launch_web(port: int = 8000, data_path: Path | None = None) -> None:
    server = create_server(port=port, data_path=data_path)
    print(f"futureRunning dashboard: http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
    finally:
        server.server_close()
