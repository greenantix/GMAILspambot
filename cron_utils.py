"""
cron_utils.py

Flexible cron-based scheduling utilities with persistent state tracking.

- Supports multiple jobs, each with its own cron expression.
- Persists last run times and job status in a JSON file.
- Utilities to check if a job is due, update last run, and handle missed runs.
- Robust error handling and logging (uses log_config.py).
- Designed for import and use by runners and other scripts.
- All functions/classes are documented with docstrings and usage examples.

Requirements:
- croniter (pip install croniter)
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
from croniter import croniter, CroniterBadCronError, CroniterBadDateError

from log_config import get_logger

DEFAULT_STATE_FILE = os.path.join("data", "automation_state.json")
ISOFORMAT = "%Y-%m-%dT%H:%M:%S.%f"

logger = get_logger(__name__)

class CronJob:
    """
    Represents a single cron-scheduled job with persistent state.

    Args:
        name (str): Unique job name.
        cron_expr (str): Cron expression (e.g., '0 3 * * 0').
        last_run (Optional[datetime]): Last run time (UTC).
        status (str): Last known status ('success', 'error', etc.).

    Example:
        job = CronJob("batch_analysis", "0 3 * * 0")
        if job.is_due():
            # Run job
            job.update_last_run()
    """
    def __init__(self, name: str, cron_expr: str, last_run: Optional[datetime] = None, status: str = "never"):
        self.name = name
        self.cron_expr = cron_expr
        self.last_run = last_run
        self.status = status

    def next_run(self, from_time: Optional[datetime] = None) -> datetime:
        """
        Calculate the next scheduled run time.

        Args:
            from_time (datetime, optional): Reference time (default: now UTC).

        Returns:
            datetime: Next scheduled run time (UTC).

        Raises:
            ValueError: If the cron expression is invalid.
        """
        ref = from_time or datetime.utcnow()
        try:
            return croniter(self.cron_expr, ref).get_next(datetime)
        except (CroniterBadCronError, CroniterBadDateError) as e:
            logger.error(f"CronJob[{self.name}]: Invalid cron expression '{self.cron_expr}': {e}")
            raise ValueError(f"Invalid cron expression: {self.cron_expr}")

    def is_due(self, now: Optional[datetime] = None) -> bool:
        """
        Check if the job is due to run.

        Args:
            now (datetime, optional): Current time (default: now UTC).

        Returns:
            bool: True if job is due, False otherwise.
        """
        now = now or datetime.utcnow()
        if self.last_run is None:
            return True
        try:
            next_run = croniter(self.cron_expr, self.last_run).get_next(datetime)
            return now >= next_run
        except (CroniterBadCronError, CroniterBadDateError) as e:
            logger.error(f"CronJob[{self.name}]: Invalid cron expression '{self.cron_expr}': {e}")
            return False

    def update_last_run(self, run_time: Optional[datetime] = None, status: str = "success"):
        """
        Update the last run time and status.

        Args:
            run_time (datetime, optional): Time to set as last run (default: now UTC).
            status (str): Status string.
        """
        self.last_run = run_time or datetime.utcnow()
        self.status = status

    def missed_runs(self, now: Optional[datetime] = None) -> int:
        """
        Calculate how many scheduled runs were missed since last_run.

        Args:
            now (datetime, optional): Current time (default: now UTC).

        Returns:
            int: Number of missed runs (0 if none).
        """
        now = now or datetime.utcnow()
        if self.last_run is None:
            return 0
        missed = 0
        ref = self.last_run
        try:
            while True:
                next_run = croniter(self.cron_expr, ref).get_next(datetime)
                if next_run > now:
                    break
                missed += 1
                ref = next_run
            return missed
        except (CroniterBadCronError, CroniterBadDateError) as e:
            logger.error(f"CronJob[{self.name}]: Invalid cron expression '{self.cron_expr}': {e}")
            return 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "cron_expr": self.cron_expr,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CronJob":
        last_run = None
        if data.get("last_run"):
            try:
                last_run = datetime.fromisoformat(data["last_run"])
            except Exception:
                last_run = None
        return cls(
            name=data["name"],
            cron_expr=data["cron_expr"],
            last_run=last_run,
            status=data.get("status", "never"),
        )

class CronScheduler:
    """
    Manages multiple cron jobs with persistent state tracking.

    Args:
        jobs_config (Dict[str, str]): Mapping of job names to cron expressions.
        state_file (str): Path to JSON file for persistent state.

    Example:
        jobs = {
            "batch_analysis": "0 3 * * 0",
            "realtime_processing": "*/15 * * * *",
            "cleanup": "0 4 * * *"
        }
        scheduler = CronScheduler(jobs)
        due_jobs = scheduler.get_due_jobs()
        for job in due_jobs:
            # Run job
            scheduler.update_job(job.name, status="success")
    """
    def __init__(self, jobs_config: Dict[str, str], state_file: str = DEFAULT_STATE_FILE):
        self.state_file = state_file
        self.jobs: Dict[str, CronJob] = {}
        self._load_jobs(jobs_config)
        self._load_state()

    def _load_jobs(self, jobs_config: Dict[str, str]):
        for name, cron_expr in jobs_config.items():
            self.jobs[name] = CronJob(name, cron_expr)

    def _load_state(self):
        if not os.path.exists(self.state_file):
            return
        try:
            with open(self.state_file, "r") as f:
                state = json.load(f)
            for name, job_data in state.items():
                if name in self.jobs:
                    self.jobs[name] = CronJob.from_dict(job_data)
        except Exception as e:
            logger.error(f"CronScheduler: Failed to load state from {self.state_file}: {e}")

    def _save_state(self):
        try:
            state = {name: job.to_dict() for name, job in self.jobs.items()}
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            with open(self.state_file, "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"CronScheduler: Failed to save state to {self.state_file}: {e}")

    def get_due_jobs(self, now: Optional[datetime] = None) -> List[CronJob]:
        """
        Get a list of jobs that are due to run.

        Args:
            now (datetime, optional): Current time (default: now UTC).

        Returns:
            List[CronJob]: List of due jobs.
        """
        now = now or datetime.utcnow()
        due = []
        for job in self.jobs.values():
            if job.is_due(now):
                due.append(job)
        return due

    def update_job(self, job_name: str, run_time: Optional[datetime] = None, status: str = "success"):
        """
        Update the last run time and status for a job, and persist state.

        Args:
            job_name (str): Name of the job.
            run_time (datetime, optional): Time to set as last run (default: now UTC).
            status (str): Status string.
        """
        if job_name not in self.jobs:
            logger.error(f"CronScheduler: No such job '{job_name}'")
            return
        self.jobs[job_name].update_last_run(run_time, status)
        self._save_state()

    def get_next_run(self, job_name: str, from_time: Optional[datetime] = None) -> Optional[datetime]:
        """
        Get the next scheduled run time for a job.

        Args:
            job_name (str): Name of the job.
            from_time (datetime, optional): Reference time (default: now UTC).

        Returns:
            datetime or None: Next run time, or None if job not found.
        """
        if job_name not in self.jobs:
            logger.error(f"CronScheduler: No such job '{job_name}'")
            return None
        try:
            return self.jobs[job_name].next_run(from_time)
        except Exception:
            return None

    def get_job_status(self, job_name: str) -> Optional[str]:
        """
        Get the last known status for a job.

        Args:
            job_name (str): Name of the job.

        Returns:
            str or None: Status string, or None if job not found.
        """
        if job_name not in self.jobs:
            logger.error(f"CronScheduler: No such job '{job_name}'")
            return None
        return self.jobs[job_name].status

    def get_last_run(self, job_name: str) -> Optional[datetime]:
        """
        Get the last run time for a job.

        Args:
            job_name (str): Name of the job.

        Returns:
            datetime or None: Last run time, or None if never run or job not found.
        """
        if job_name not in self.jobs:
            logger.error(f"CronScheduler: No such job '{job_name}'")
            return None
        return self.jobs[job_name].last_run

    def get_missed_runs(self, job_name: str, now: Optional[datetime] = None) -> int:
        """
        Get the number of missed runs for a job since last run.

        Args:
            job_name (str): Name of the job.
            now (datetime, optional): Current time (default: now UTC).

        Returns:
            int: Number of missed runs, or 0 if job not found.
        """
        if job_name not in self.jobs:
            logger.error(f"CronScheduler: No such job '{job_name}'")
            return 0
        return self.jobs[job_name].missed_runs(now)

    def reload(self):
        """
        Reload state from the state file (useful if state may be updated externally).
        """
        self._load_state()

    def save(self):
        """
        Save current state to the state file.
        """
        self._save_state()

# =========================
# Usage Example
# =========================
if False:
    # Example usage (not executed)
    from log_config import init_logging
    init_logging()
    jobs = {
        "batch_analysis": "0 3 * * 0",
        "realtime_processing": "*/15 * * * *",
        "cleanup": "0 4 * * *"
    }
    scheduler = CronScheduler(jobs)
    due_jobs = scheduler.get_due_jobs()
    for job in due_jobs:
        print(f"Running job: {job.name}")
        # ... run the job ...
        scheduler.update_job(job.name, status="success")