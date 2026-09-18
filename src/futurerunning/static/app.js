const $ = (id) => document.getElementById(id);
const today = new Date().toISOString().slice(0, 10);
$('runDate').value = today;
$('end').value = today;
$('start').value = today.slice(0, 8) + '01';

function pace(seconds) {
  if (seconds == null) return '--';
  seconds = Math.round(seconds);
  return Math.floor(seconds / 60) + ':' + String(seconds % 60).padStart(2, '0') + ' /mi';
}

function duration(seconds) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor(seconds % 3600 / 60);
  const remainder = seconds % 60;
  return hours ? `${hours}h ${String(minutes).padStart(2, '0')}m` : `${minutes}m ${String(remainder).padStart(2, '0')}s`;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' })[character]);
}

document.querySelectorAll('[data-view]').forEach(button => {
  button.onclick = () => {
    document.querySelectorAll('.view').forEach(view => view.classList.remove('active'));
    document.querySelectorAll('.nav button').forEach(item => item.classList.remove('active'));
    $(button.dataset.view).classList.add('active');
    button.classList.add('active');
  };
});

async function refresh() {
  const data = await (await fetch('/api/state')).json();
  const summary = data.summary;
  $('title').textContent = (data.profile_name || 'Your') + "'s running journal";
  $('runs').textContent = summary.run_count;
  $('miles').textContent = summary.total_miles.toFixed(1) + ' mi';
  $('pace').textContent = pace(summary.average_pace_seconds);
  $('longest').textContent = summary.longest_run_miles.toFixed(1) + ' mi';
  $('streak').textContent = data.streak + ' days';
  $('logRuns').textContent = summary.run_count;
  $('logMiles').textContent = summary.total_miles.toFixed(1) + ' mi';
  $('logPace').textContent = pace(summary.average_pace_seconds);
  $('logStreak').textContent = data.streak + ' days';
  $('name').value = data.profile_name || '';
  const progress = data.goal_progress;
  $('goalStatus').textContent = progress ? `Goal: ${progress.completed.toFixed(1)}/${data.goal.target_miles.toFixed(1)} mi (${progress.percentage.toFixed(0)}%)` : 'No goal set yet.';
  $('overviewGoal').textContent = progress ? `Goal progress: ${progress.completed.toFixed(1)} of ${data.goal.target_miles.toFixed(1)} miles completed.` : 'Set a mileage goal in the Goals view when you are ready.';
  $('progressBar').style.width = (progress ? progress.percentage : 0) + '%';
  $('table').innerHTML = data.runs.length ? `<table><thead><tr><th>Date</th><th>Distance</th><th>Time</th><th>Pace</th><th>Notes</th><th></th></tr></thead><tbody>${data.runs.map(run => `<tr><td>${escapeHtml(run.run_date)}</td><td>${run.distance_miles.toFixed(2)} mi</td><td>${duration(run.duration_seconds)}</td><td>${pace(run.pace_seconds_per_mile)}</td><td>${escapeHtml(run.notes || '')}</td><td><button class="danger" onclick="removeRun('${escapeHtml(run.id)}')">Delete</button></td></tr>`).join('')}</tbody></table>` : '<div class="empty">No runs yet. Log your first run to build your history.</div>';
}

async function removeRun(id) {
  if (confirm('Delete this run?')) {
    await fetch('/api/runs/' + id, { method: 'DELETE' });
    refresh();
  }
}

$('run').onsubmit = async event => {
  event.preventDefault();
  $('status').textContent = '';
  const hours = Number($('hours').value || 0);
  const minutes = Number($('minutes').value || 0);
  const seconds = Number($('seconds').value || 0);
  if (minutes > 59 || seconds > 59 || hours < 0 || minutes < 0 || seconds < 0 || hours + minutes + seconds === 0) {
    $('status').textContent = 'Please enter how long the run took.';
    return;
  }
  const response = await fetch('/api/runs', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ distance: $('distance').value, duration: `${hours}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`, run_date: $('runDate').value, notes: $('notes').value }) });
  const result = await response.json();
  if (!response.ok) { $('status').textContent = result.error; return; }
  event.target.reset();
  $('hours').value = 0; $('minutes').value = 0; $('seconds').value = 0; $('runDate').value = today;
  await refresh();
  document.querySelector('[data-view="overview"]').click();
};

$('profile').onsubmit = async event => {
  event.preventDefault();
  await fetch('/api/profile', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: $('name').value }) });
  refresh();
};

$('goal').onsubmit = async event => {
  event.preventDefault();
  const response = await fetch('/api/goal', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ miles: $('target').value, start: $('start').value, end: $('end').value }) });
  const result = await response.json();
  if (!response.ok) { $('goalStatus').textContent = result.error; return; }
  refresh();
};

refresh();
