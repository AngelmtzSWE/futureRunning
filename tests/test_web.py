import json
import tempfile
import threading
import unittest
from datetime import date
from http.client import HTTPConnection
from pathlib import Path

from futurerunning.web import create_server


class WebApiTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.server = create_server(port=0, data_path=Path(self.temp_directory.name) / "runs.json")
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.connection = HTTPConnection("127.0.0.1", self.server.server_port)

    def tearDown(self):
        self.connection.close()
        self.server.shutdown()
        self.server.server_close()
        self.temp_directory.cleanup()

    def request(self, method, path, payload=None):
        body = json.dumps(payload).encode() if payload is not None else None
        headers = {"Content-Type": "application/json"} if body else {}
        self.connection.request(method, path, body, headers)
        response = self.connection.getresponse()
        content = response.read()
        return response.status, json.loads(content) if content else None

    def test_dashboard_api_supports_personal_run_workflow(self):
        status, state = self.request("GET", "/api/state")
        self.assertEqual(status, 200)
        self.assertEqual(state["summary"]["run_count"], 0)

        status, _ = self.request("POST", "/api/profile", {"name": "Jamie"})
        self.assertEqual(status, 200)
        status, _ = self.request("POST", "/api/runs", {"distance": 3.1, "duration": "0:28:30", "run_date": date.today().isoformat(), "notes": "<script>"})
        self.assertEqual(status, 200)
        status, state = self.request("GET", "/api/state")
        self.assertEqual(status, 200)
        self.assertEqual(state["profile_name"], "Jamie")
        self.assertEqual(state["summary"]["run_count"], 1)
        self.assertEqual(state["runs"][0]["notes"], "<script>")

    def test_dashboard_api_rejects_invalid_run_duration(self):
        status, payload = self.request("POST", "/api/runs", {"distance": 3, "duration": "3:90", "run_date": date.today().isoformat()})
        self.assertEqual(status, 400)
        self.assertIn("seconds", payload["error"])


if __name__ == "__main__":
    unittest.main()
