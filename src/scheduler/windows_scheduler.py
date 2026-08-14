import subprocess
import os
import sys

class WindowsScheduler:
    def __init__(self, project_root: str, task_name: str = "IncrementalGitHubPublisher"):
        self.project_root = os.path.abspath(project_root)
        self.task_name = task_name
        self.python_exe = sys.executable
        # Get path to cli main script
        self.script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "cli", "main.py"))

    def schedule_daily(self, time: str = "09:00"):
        """Schedules the publisher to run daily at a specific time and on startup (for missed runs)."""
        cmd = f'"{self.python_exe}" "{self.script_path}" release --dir "{self.project_root}"'
        
        # schtasks command to create a daily task
        # /sc daily /tn TaskName /tr "command" /st HH:mm
        subprocess.run([
            "schtasks", "/create", "/tn", self.task_name,
            "/tr", cmd, "/sc", "daily", "/st", time, "/f"
        ], capture_output=True, text=True)

        print(f"Scheduled daily task '{self.task_name}' at {time}.")

    def remove_schedule(self):
        """Removes the scheduled task."""
        subprocess.run([
            "schtasks", "/delete", "/tn", self.task_name, "/f"
        ], capture_output=True, text=True)
        print(f"Removed scheduled task '{self.task_name}'.")
