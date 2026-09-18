import tkinter as tk
from datetime import date
from pathlib import Path
from tkinter import messagebox, ttk

from .models import Goal, Run
from .services import current_streak, goal_progress, summarize
from .storage import RunStore


class FutureRunningApp(tk.Tk):
    """Desktop dashboard for a personal futureRunning journal."""

    COLORS = {
        "ink": "#17231f",
        "muted": "#66736d",
        "paper": "#f5f1e9",
        "panel": "#fffdf8",
        "accent": "#d76543",
        "accent_dark": "#a8412b",
        "sage": "#dce8dc",
        "line": "#d8d5cc",
    }

    def __init__(self, data_path: Path | None = None) -> None:
        super().__init__()
        self.store = RunStore(data_path or Path(".futurerunning/runs.json"))
        self.runs, self.goal = self.store.load()
        self.profile_name = self.store.get_profile_name()
        self.title("futureRunning | Your running journal")
        self.geometry("1120x760")
        self.minsize(900, 650)
        self.configure(bg=self.COLORS["paper"])
        self._configure_styles()
        self._build_layout()
        self._refresh()

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("App.TFrame", background=self.COLORS["paper"])
        style.configure("Panel.TFrame", background=self.COLORS["panel"])
        style.configure("Title.TLabel", background=self.COLORS["paper"], foreground=self.COLORS["ink"], font=("Helvetica", 28, "bold"))
        style.configure("Subtitle.TLabel", background=self.COLORS["paper"], foreground=self.COLORS["muted"], font=("Helvetica", 11))
        style.configure("PanelTitle.TLabel", background=self.COLORS["panel"], foreground=self.COLORS["ink"], font=("Helvetica", 13, "bold"))
        style.configure("Metric.TLabel", background=self.COLORS["panel"], foreground=self.COLORS["accent_dark"], font=("Helvetica", 20, "bold"))
        style.configure("MetricName.TLabel", background=self.COLORS["panel"], foreground=self.COLORS["muted"], font=("Helvetica", 9))
        style.configure("TLabel", background=self.COLORS["panel"], foreground=self.COLORS["ink"], font=("Helvetica", 10))
        style.configure("TEntry", padding=7)
        style.configure("Accent.TButton", background=self.COLORS["accent"], foreground="white", padding=(12, 8), font=("Helvetica", 10, "bold"))
        style.map("Accent.TButton", background=[("active", self.COLORS["accent_dark"])])
        style.configure("Quiet.TButton", padding=(10, 7))
        style.configure("Treeview", rowheight=30, font=("Helvetica", 10), background=self.COLORS["panel"], fieldbackground=self.COLORS["panel"])
        style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"))

    def _build_layout(self) -> None:
        root = ttk.Frame(self, style="App.TFrame", padding=28)
        root.pack(fill="both", expand=True)
        header = ttk.Frame(root, style="App.TFrame")
        header.pack(fill="x", pady=(0, 22))
        self.greeting = ttk.Label(header, style="Title.TLabel")
        self.greeting.pack(anchor="w")
        ttk.Label(header, text="A clear view of your effort, one run at a time.", style="Subtitle.TLabel").pack(anchor="w", pady=(4, 0))

        content = ttk.Frame(root, style="App.TFrame")
        content.pack(fill="both", expand=True)
        content.columnconfigure(0, weight=3)
        content.columnconfigure(1, weight=2)
        content.rowconfigure(1, weight=1)

        metrics = ttk.Frame(content, style="App.TFrame")
        metrics.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 18))
        for index in range(5):
            metrics.columnconfigure(index, weight=1)
            panel = ttk.Frame(metrics, style="Panel.TFrame", padding=14)
            panel.grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 6, 0))
            value = ttk.Label(panel, style="Metric.TLabel")
            value.pack(anchor="w")
            label = ttk.Label(panel, style="MetricName.TLabel")
            label.pack(anchor="w", pady=(5, 0))
            setattr(self, f"metric_{index}", value)
            setattr(self, f"metric_label_{index}", label)

        history = ttk.Frame(content, style="Panel.TFrame", padding=18)
        history.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        history.rowconfigure(1, weight=1)
        history.columnconfigure(0, weight=1)
        ttk.Label(history, text="Your runs", style="PanelTitle.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 12))
        columns = ("date", "distance", "duration", "pace", "notes")
        self.runs_table = ttk.Treeview(history, columns=columns, show="headings", selectmode="browse")
        headings = {"date": "Date", "distance": "Distance", "duration": "Time", "pace": "Pace", "notes": "Notes"}
        widths = {"date": 100, "distance": 85, "duration": 100, "pace": 90, "notes": 180}
        for column in columns:
            self.runs_table.heading(column, text=headings[column])
            self.runs_table.column(column, width=widths[column], anchor="w")
        self.runs_table.grid(row=1, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(history, orient="vertical", command=self.runs_table.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.runs_table.configure(yscrollcommand=scrollbar.set)
        ttk.Button(history, text="Delete selected run", style="Quiet.TButton", command=self._delete_selected).grid(row=2, column=0, sticky="w", pady=(12, 0))

        side = ttk.Frame(content, style="App.TFrame")
        side.grid(row=1, column=1, sticky="nsew")
        side.rowconfigure(2, weight=1)
        self._build_form(side)

    def _build_form(self, parent: ttk.Frame) -> None:
        profile = ttk.Frame(parent, style="Panel.TFrame", padding=18)
        profile.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        ttk.Label(profile, text="Your profile", style="PanelTitle.TLabel").pack(anchor="w")
        self.name_entry = ttk.Entry(profile)
        self.name_entry.insert(0, self.profile_name)
        self.name_entry.pack(fill="x", pady=(10, 8))
        ttk.Button(profile, text="Save name", command=self._save_profile).pack(anchor="e")

        add = ttk.Frame(parent, style="Panel.TFrame", padding=18)
        add.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        ttk.Label(add, text="Log a run", style="PanelTitle.TLabel").pack(anchor="w")
        self.distance_entry = self._field(add, "Distance (miles)", "e.g. 3.1")
        self.duration_entry = self._field(add, "Time (MM:SS or H:MM:SS)", "e.g. 28:30")
        self.date_entry = self._field(add, "Date (YYYY-MM-DD)", date.today().isoformat())
        self.notes_entry = self._field(add, "Notes (optional)", "")
        ttk.Button(add, text="Add run", style="Accent.TButton", command=self._add_run).pack(fill="x", pady=(14, 0))

        goal = ttk.Frame(parent, style="Panel.TFrame", padding=18)
        goal.grid(row=2, column=0, sticky="new")
        ttk.Label(goal, text="Set a mileage goal", style="PanelTitle.TLabel").pack(anchor="w")
        self.goal_miles = self._field(goal, "Target miles", "e.g. 40")
        self.goal_start = self._field(goal, "Start date", date.today().replace(day=1).isoformat())
        self.goal_end = self._field(goal, "End date", date.today().isoformat())
        ttk.Button(goal, text="Save goal", command=self._save_goal).pack(fill="x", pady=(14, 0))
        self.goal_status = ttk.Label(goal, style="Subtitle.TLabel", wraplength=300)
        self.goal_status.pack(anchor="w", pady=(12, 0))

    def _field(self, parent: ttk.Frame, label: str, placeholder: str) -> ttk.Entry:
        ttk.Label(parent, text=label).pack(anchor="w", pady=(10, 4))
        entry = ttk.Entry(parent)
        entry.insert(0, placeholder)
        entry.pack(fill="x")
        return entry

    def _refresh(self) -> None:
        name = self.profile_name or "Runner"
        self.greeting.configure(text=f"{name}'s running journal")
        summary = summarize(self.runs)
        values = (str(summary.run_count), f"{summary.total_miles:.1f} mi", summary.average_pace_display, f"{summary.longest_run_miles:.1f} mi", f"{current_streak(self.runs)} days")
        labels = ("Runs logged", "Total distance", "Average pace", "Longest run", "Current streak")
        for index, (value, label) in enumerate(zip(values, labels)):
            getattr(self, f"metric_{index}").configure(text=value)
            getattr(self, f"metric_label_{index}").configure(text=label)
        for item in self.runs_table.get_children():
            self.runs_table.delete(item)
        for run in sorted(self.runs, key=lambda item: item.run_date, reverse=True):
            self.runs_table.insert("", "end", iid=run.id, values=(run.run_date, f"{run.distance_miles:.2f} mi", run.duration_display, run.pace_display, run.notes))
        progress = goal_progress(self.runs, self.goal)
        self.goal_status.configure(text=(f"Goal: {progress[0]:.1f}/{self.goal.target_miles:.1f} mi ({progress[1]:.0f}%)" if progress else "No goal set yet."))

    def _save_profile(self) -> None:
        self.profile_name = self.name_entry.get().strip() or "Runner"
        self.store.set_profile_name(self.profile_name)
        self._refresh()

    def _add_run(self) -> None:
        try:
            distance = float(self.distance_entry.get())
            duration_parts = [int(part) for part in self.duration_entry.get().split(":")]
            if len(duration_parts) == 2:
                duration = duration_parts[0] * 60 + duration_parts[1]
            elif len(duration_parts) == 3:
                duration = duration_parts[0] * 3600 + duration_parts[1] * 60 + duration_parts[2]
            else:
                raise ValueError("time must be MM:SS or H:MM:SS")
            if any(part < 0 for part in duration_parts) or duration_parts[-1] >= 60 or (len(duration_parts) == 3 and duration_parts[1] >= 60):
                raise ValueError("time has invalid minute or second values")
            run = Run(distance, duration, self.date_entry.get().strip(), self.notes_entry.get().strip())
            self.store.add(run)
            self.runs, self.goal = self.store.load()
            self._refresh()
            self.distance_entry.delete(0, "end")
            self.duration_entry.delete(0, "end")
            self.notes_entry.delete(0, "end")
        except (ValueError, IndexError) as error:
            messagebox.showerror("Could not add run", str(error))

    def _save_goal(self) -> None:
        try:
            self.goal = Goal(float(self.goal_miles.get()), self.goal_start.get().strip(), self.goal_end.get().strip())
            self.store.set_goal(self.goal)
            self._refresh()
        except ValueError as error:
            messagebox.showerror("Could not save goal", str(error))

    def _delete_selected(self) -> None:
        selected = self.runs_table.selection()
        if selected and messagebox.askyesno("Delete run", "Delete this run from your journal?"):
            self.store.delete(selected[0])
            self.runs, self.goal = self.store.load()
            self._refresh()


def launch_gui(data_path: Path | None = None) -> None:
    app = FutureRunningApp(data_path)
    app.mainloop()
