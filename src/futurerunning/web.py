import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .models import Goal, Run
from .services import current_streak, goal_progress, summarize
from .storage import RunStore


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>futureRunning</title>
<style>
:root{--ink:#17231f;--muted:#66736d;--paper:#f5f1e9;--panel:#fffdf8;--accent:#d76543;--dark:#a8412b;--line:#d8d5cc;--sage:#dce8dc}
*{box-sizing:border-box}body{margin:0;color:var(--ink);background:var(--paper);font:15px Georgia,serif}.shell{max-width:1160px;margin:auto;padding:34px 24px 70px}header{display:flex;align-items:end;justify-content:space-between;gap:24px;margin-bottom:24px}h1{font-size:clamp(2.5rem,6vw,5rem);line-height:.9;margin:0 0 12px;letter-spacing:-3px}h2{margin:0 0 16px;font-size:1.3rem}.sub,.hint,.status{color:var(--muted)}.sub{font-size:1.1rem}.nav{display:flex;gap:6px;flex-wrap:wrap}.nav button{background:transparent;color:var(--muted);border:1px solid var(--line);padding:9px 12px}.nav button.active{background:var(--ink);color:#fff;border-color:var(--ink)}.view{display:none}.view.active{display:block}.panel,.metric{background:var(--panel);border:1px solid var(--line);padding:22px;border-radius:8px}.grid{display:grid;gap:16px}.metrics{grid-template-columns:repeat(5,1fr);margin-bottom:18px}.metric strong{display:block;color:var(--dark);font-size:1.7rem;margin-bottom:5px}.metric span{color:var(--muted);font-size:.85rem}.log-layout{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(260px,.85fr);gap:18px;align-items:start}.log-hero{padding:clamp(26px,5vw,52px);background:var(--ink);color:#fff}.log-hero h2{font-size:clamp(2rem,4vw,3.4rem);line-height:1;margin-bottom:12px}.log-hero .hint{color:#b7c6bd}.log-hero label{color:#dce8dc}.log-hero input{background:#fff}.form{display:grid;gap:13px}label{display:grid;gap:6px;color:var(--muted);font-size:.9rem}input{width:100%;padding:12px;border:1px solid var(--line);border-radius:5px;background:#fff;color:var(--ink);font:inherit}button{border:0;border-radius:5px;padding:12px 15px;cursor:pointer;font:600 14px Georgia,serif;background:var(--accent);color:#fff}button.secondary{background:var(--sage);color:var(--ink)}button.danger{background:transparent;color:var(--dark);padding:4px 7px}.log-hero button{font-size:1rem;margin-top:5px}.quick{display:grid;gap:12px}.quick .row{display:flex;justify-content:space-between;border-bottom:1px solid var(--line);padding-bottom:10px}.table-wrap{overflow-x:auto}table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:12px 8px;border-bottom:1px solid var(--line)}th{color:var(--muted);font-size:.78rem;text-transform:uppercase;letter-spacing:.5px}.empty{color:var(--muted);padding:28px 0}.goal-layout{display:grid;grid-template-columns:minmax(0,.8fr) minmax(280px,1.2fr);gap:18px}.goal-card{background:var(--sage);border-radius:8px;padding:25px}.progress{height:12px;background:#fff;border-radius:20px;overflow:hidden;margin:18px 0}.progress i{display:block;height:100%;background:var(--accent);width:0}.profile{margin-top:16px;padding-top:16px;border-top:1px solid var(--line)}
 .time-row{display:grid;grid-template-columns:repeat(3,1fr);gap:9px}.time-row input{font-size:1.2rem;padding:14px}.time-row label{color:var(--muted);font-size:.82rem}.log-hero .time-row label{color:#dce8dc}@media(max-width:800px){header{display:block}.nav{margin-top:20px}.metrics{grid-template-columns:repeat(2,1fr)}.log-layout,.goal-layout{grid-template-columns:1fr}}@media(max-width:500px){.shell{padding:24px 15px}.metrics{grid-template-columns:1fr 1fr}th:nth-child(3),td:nth-child(3),th:nth-child(5),td:nth-child(5){display:none}}
</style></head><body><main class="shell">
<header><div><h1 id="title">Your running journal</h1><div class="sub">A clear view of your effort, one run at a time.</div></div><nav class="nav"><button data-view="log" class="active">Log a run</button><button data-view="overview">Overview</button><button data-view="history">History</button><button data-view="goals">Goals</button></nav></header>
<section id="log" class="view active"><div class="log-layout"><div class="panel log-hero"><div class="hint">TODAY'S MOMENT</div><h2>Log your run.</h2><p class="hint">Tell us three simple things. We will do the math.</p><form id="run" class="form"><label>How far did you go? <span class="hint">miles</span><input id="distance" type="number" min="0.01" step="0.01" placeholder="Example: 3.1" required></label><div><label>How long did it take?</label><div class="time-row"><label>Hours<input id="hours" type="number" min="0" max="99" value="0" aria-label="Hours"></label><label>Minutes<input id="minutes" type="number" min="0" max="59" value="0" aria-label="Minutes"></label><label>Seconds<input id="seconds" type="number" min="0" max="59" value="0" aria-label="Seconds"></label></div></div><label>When did you run?<input id="runDate" type="date" required></label><label>Anything you want to remember? <span class="hint">optional</span><input id="notes" placeholder="Example: Felt strong"></label><button>Add my run</button><div class="status" id="status"></div></form></div><div class="panel"><h2>Your rhythm</h2><div class="quick"><div class="row"><span>Runs logged</span><strong id="logRuns">0</strong></div><div class="row"><span>Total distance</span><strong id="logMiles">0.0 mi</strong></div><div class="row"><span>Average pace</span><strong id="logPace">--</strong></div><div class="row"><span>Current streak</span><strong id="logStreak">0 days</strong></div></div><p class="hint" style="margin-top:28px">Your data stays local in this project. No account or upload required.</p></div></div></section>
<section id="overview" class="view"><div class="grid metrics"><div class="metric"><strong id="runs">0</strong><span>Runs logged</span></div><div class="metric"><strong id="miles">0.0 mi</strong><span>Total distance</span></div><div class="metric"><strong id="pace">--</strong><span>Average pace</span></div><div class="metric"><strong id="longest">0.0 mi</strong><span>Longest run</span></div><div class="metric"><strong id="streak">0 days</strong><span>Current streak</span></div></div><div class="panel"><h2>Training snapshot</h2><p class="sub">Your consistency, measured in the metrics that matter.</p><div id="overviewGoal" class="status"></div></div></section>
<section id="history" class="view"><div class="panel"><h2>Run history</h2><p class="sub">Every run you have logged, in one place.</p><div id="table" class="table-wrap"></div></div></section>
<section id="goals" class="view"><div class="goal-layout"><div class="panel"><h2>Personalize your journal</h2><form id="profile" class="form"><label>Your name<input id="name" placeholder="e.g. Alex"></label><button class="secondary">Save name</button></form><div class="profile"><p class="hint">This journal belongs to you. Your name is saved locally with your running data.</p></div></div><div class="panel"><h2>Set a mileage goal</h2><form id="goal" class="form"><label>Target miles<input id="target" type="number" min="0.1" step="0.1" placeholder="40"></label><label>Start date<input id="start" type="date"></label><label>End date<input id="end" type="date"></label><button>Save goal</button></form><div class="goal-card" style="margin-top:18px"><strong id="goalStatus">No goal set yet.</strong><div class="progress"><i id="progressBar"></i></div><span class="hint">Build a goal around your own season, not someone else's.</span></div></div></div></section>
</main><script>
const $=id=>document.getElementById(id), today=new Date().toISOString().slice(0,10);$('runDate').value=today;$('end').value=today;$('start').value=today.slice(0,8)+'01';
function pace(s){if(s==null)return'--';s=Math.round(s);return Math.floor(s/60)+':'+String(s%60).padStart(2,'0')+' /mi'}function duration(s){let h=Math.floor(s/3600),m=Math.floor(s%3600/60),x=s%60;return h?`${h}h ${String(m).padStart(2,'0')}m`:`${m}m ${String(x).padStart(2,'0')}s`}
document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>{document.querySelectorAll('.view').forEach(v=>v.classList.remove('active'));document.querySelectorAll('.nav button').forEach(x=>x.classList.remove('active'));$(b.dataset.view).classList.add('active');b.classList.add('active')});
async function refresh(){const d=await(await fetch('/api/state')).json(),s=d.summary;$('title').textContent=(d.profile_name||'Your')+"'s running journal";['runs','miles','pace','longest','streak'].forEach((id,i)=>$(id).textContent=[s.run_count,s.total_miles.toFixed(1)+' mi',pace(s.average_pace_seconds),s.longest_run_miles.toFixed(1)+' mi',d.streak+' days'][i]);$('logRuns').textContent=s.run_count;$('logMiles').textContent=s.total_miles.toFixed(1)+' mi';$('logPace').textContent=pace(s.average_pace_seconds);$('logStreak').textContent=d.streak+' days';$('name').value=d.profile_name||'';let p=d.goal_progress;$('goalStatus').textContent=p?`Goal: ${p.completed.toFixed(1)}/${d.goal.target_miles.toFixed(1)} mi (${p.percentage.toFixed(0)}%)`:'No goal set yet.';$('overviewGoal').textContent=p?`Goal progress: ${p.completed.toFixed(1)} of ${d.goal.target_miles.toFixed(1)} miles completed.`:'Set a mileage goal in the Goals view when you are ready.';$('progressBar').style.width=(p?p.percentage:0)+'%';$('table').innerHTML=d.runs.length?`<table><thead><tr><th>Date</th><th>Distance</th><th>Time</th><th>Pace</th><th>Notes</th><th></th></tr></thead><tbody>${d.runs.map(r=>`<tr><td>${r.run_date}</td><td>${r.distance_miles.toFixed(2)} mi</td><td>${duration(r.duration_seconds)}</td><td>${pace(r.pace_seconds_per_mile)}</td><td>${r.notes||''}</td><td><button class="danger" onclick="removeRun('${r.id}')">Delete</button></td></tr>`).join('')}</tbody></table>`:'<div class="empty">No runs yet. Log your first run to build your history.</div>'}
async function removeRun(id){if(confirm('Delete this run?')){await fetch('/api/runs/'+id,{method:'DELETE'});refresh()}}$('run').onsubmit=async e=>{e.preventDefault();$('status').textContent='';let h=Number($('hours').value||0),m=Number($('minutes').value||0),s=Number($('seconds').value||0);if(m>59||s>59||h<0||m<0||s<0||h+m+s===0){$('status').textContent='Please enter how long the run took.';return}let r=await fetch('/api/runs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({distance:$('distance').value,duration:`${h}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`,run_date:$('runDate').value,notes:$('notes').value})}),o=await r.json();if(!r.ok){$('status').textContent=o.error;return}e.target.reset();$('hours').value=0;$('minutes').value=0;$('seconds').value=0;$('runDate').value=today;await refresh();document.querySelector('[data-view="overview"]').click()};$('profile').onsubmit=async e=>{e.preventDefault();await fetch('/api/profile',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:$('name').value})});refresh()};$('goal').onsubmit=async e=>{e.preventDefault();let r=await fetch('/api/goal',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({miles:$('target').value,start:$('start').value,end:$('end').value})}),o=await r.json();if(!r.ok){$('goalStatus').textContent=o.error;return}refresh()};refresh();
</script></body></html>"""


def _duration(value: str) -> int:
    parts = [int(part) for part in value.split(":")]
    if len(parts) == 2:
        minutes, seconds = parts
        if seconds >= 60: raise ValueError("seconds must be below 60")
        return minutes * 60 + seconds
    if len(parts) == 3:
        hours, minutes, seconds = parts
        if minutes >= 60 or seconds >= 60: raise ValueError("minutes and seconds must be below 60")
        return hours * 3600 + minutes * 60 + seconds
    raise ValueError("time must be MM:SS or H:MM:SS")


def create_server(host: str = "0.0.0.0", port: int = 8000, data_path: Path | None = None) -> ThreadingHTTPServer:
    store = RunStore(data_path or Path(".futurerunning/runs.json"))

    class Handler(BaseHTTPRequestHandler):
        def send_json(self, payload: object, status: int = 200) -> None:
            body = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def read_json(self) -> dict:
            length = int(self.headers.get("Content-Length", 0))
            return json.loads(self.rfile.read(length))

        def do_GET(self) -> None:
            if self.path == "/":
                body = PAGE.encode()
                self.send_response(200); self.send_header("Content-Type", "text/html"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body); return
            if self.path == "/api/state":
                runs, goal = store.load(); summary = summarize(runs)
                self.send_json({"profile_name": store.get_profile_name(), "runs": [{**run.to_dict(), "pace_seconds_per_mile": run.pace_seconds_per_mile} for run in sorted(runs, key=lambda item: item.run_date, reverse=True)], "summary": {"run_count": summary.run_count, "total_miles": summary.total_miles, "total_seconds": summary.total_seconds, "average_pace_seconds": summary.average_pace_seconds, "longest_run_miles": summary.longest_run_miles}, "streak": current_streak(runs), "goal": goal.to_dict() if goal else None, "goal_progress": ({"completed": goal_progress(runs, goal)[0], "percentage": goal_progress(runs, goal)[1]} if goal else None)})
                return
            self.send_error(404)

        def do_POST(self) -> None:
            try:
                data = self.read_json()
                runs, goal = store.load()
                if self.path == "/api/runs":
                    run = Run(float(data["distance"]), _duration(str(data["duration"])), str(data["run_date"]), str(data.get("notes", "")))
                    store.add(run)
                elif self.path == "/api/profile":
                    store.set_profile_name(str(data.get("name", "")))
                elif self.path == "/api/goal":
                    store.set_goal(Goal(float(data["miles"]), str(data["start"]), str(data["end"])))
                else: self.send_error(404); return
                self.send_json({"ok": True})
            except (ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
                self.send_json({"error": str(error)}, 400)

        def do_DELETE(self) -> None:
            if self.path.startswith("/api/runs/"):
                store.delete(self.path.rsplit("/", 1)[-1]); self.send_json({"ok": True}); return
            self.send_error(404)

        def log_message(self, *_args) -> None:
            return

    return ThreadingHTTPServer((host, port), Handler)


def launch_web(port: int = 8000, data_path: Path | None = None) -> None:
    server = create_server(port=port, data_path=data_path)
    print(f"futureRunning dashboard: http://localhost:{port}")
    try: server.serve_forever()
    except KeyboardInterrupt: print("\nDashboard stopped.")
    finally: server.server_close()
