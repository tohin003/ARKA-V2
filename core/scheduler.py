"""
core/scheduler.py — The Heartbeat (Phase 5.2)

A background daemon thread that runs scheduled jobs while the user
is idle in the main REPL loop. This is ARKA's "subconscious".

Architecture:
    - Main Thread: User interaction (input/output)
    - Daemon Thread: Scheduler loop (runs jobs at intervals)
    - Communication: threading.Event for graceful shutdown
"""

import threading
import datetime
import schedule
import time
import structlog

logger = structlog.get_logger()


class HeartbeatScheduler:
    """
    Manages background scheduled tasks for ARKA.
    Runs as a daemon thread so it dies when main thread exits.
    """

    def __init__(self):
        self._stop_event = threading.Event()
        self._thread = None
        self._jobs_registered = 0
        self._pulse_count = 0

    # ─── Job Definitions ──────────────────────────────────────────────

    def _pulse(self):
        """Core heartbeat tick. Runs every interval."""
        self._pulse_count += 1
        now = datetime.datetime.now()
        logger.info(
            "heartbeat_pulse",
            pulse=self._pulse_count,
            time=now.strftime("%H:%M:%S"),
        )

    def _morning_briefing(self):
        """
        Morning briefing job. Runs at 9:00 AM.
        Currently logs a placeholder; will be wired to Weather/Calendar tools later.
        """
        now = datetime.datetime.now()
        logger.info("heartbeat_morning_briefing", time=now.strftime("%H:%M"))
        print(f"\n🌅 [Heartbeat] Good morning, Commander! It's {now.strftime('%I:%M %p')}.")
        print("   📋 TODO: Wire up Calendar + Weather checks here.")
        print("   Type your command below.\n")

    def _evening_summary(self):
        """
        Evening summary job. Runs at 9:00 PM.
        """
        now = datetime.datetime.now()
        logger.info("heartbeat_evening_summary", time=now.strftime("%H:%M"))
        print(f"\n🌙 [Heartbeat] Good evening! Session summary at {now.strftime('%I:%M %p')}.")
        print("   📊 TODO: Wire up session stats / learnings summary here.\n")

    def _learn_patterns(self):
        """Pattern learning job (Phase 6.1). Runs every 30 min."""
        try:
            from core.pattern_learner import pattern_learner
            new_patterns = pattern_learner.learn()
            if new_patterns:
                logger.info("heartbeat_patterns_discovered", count=len(new_patterns))
        except Exception as e:
            logger.error("heartbeat_pattern_error", error=str(e))

    # ─── Registration ─────────────────────────────────────────────────

    def register_default_jobs(self):
        """Register all default heartbeat jobs."""
        # Pulse: every 5 minutes (lightweight health check)
        schedule.every(5).minutes.do(self._pulse)
        self._jobs_registered += 1

        # Morning Briefing: 9:00 AM daily
        schedule.every().day.at("09:00").do(self._morning_briefing)
        self._jobs_registered += 1

        # Evening Summary: 9:00 PM daily
        schedule.every().day.at("21:00").do(self._evening_summary)
        self._jobs_registered += 1

        # Pattern Learning: every 30 minutes (Phase 6.1)
        schedule.every(30).minutes.do(self._learn_patterns)
        self._jobs_registered += 1

        logger.info(
            "heartbeat_jobs_registered",
            count=self._jobs_registered,
        )

    def register_job(self, job_func, interval_minutes=None, at_time=None):
        """
        Register a custom job.
        
        Args:
            job_func: Callable to execute.
            interval_minutes: Run every N minutes (mutually exclusive with at_time).
            at_time: Run at a specific time daily, e.g. "14:30" (mutually exclusive with interval_minutes).
        """
        if interval_minutes:
            schedule.every(interval_minutes).minutes.do(job_func)
        elif at_time:
            schedule.every().day.at(at_time).do(job_func)
        else:
            raise ValueError("Must specify either interval_minutes or at_time.")
        self._jobs_registered += 1
        logger.info("heartbeat_custom_job_registered", job=job_func.__name__)

    # ─── Thread Control ───────────────────────────────────────────────

    def _run_loop(self):
        """The actual loop that runs in the background thread."""
        logger.info("heartbeat_started")
        while not self._stop_event.is_set():
            schedule.run_pending()
            # Sleep in small increments so we can respond to stop quickly
            self._stop_event.wait(timeout=1.0)
        logger.info("heartbeat_stopped")

    def start(self):
        """Start the heartbeat daemon thread."""
        if self._thread and self._thread.is_alive():
            logger.warning("heartbeat_already_running")
            return

        self.register_default_jobs()
        self._thread = threading.Thread(
            target=self._run_loop,
            name="ARKA-Heartbeat",
            daemon=True,  # Dies when main thread exits
        )
        self._thread.start()
        logger.info("heartbeat_thread_launched", thread=self._thread.name)

    def stop(self):
        """Gracefully stop the heartbeat."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=3.0)
        schedule.clear()
        logger.info("heartbeat_shutdown_complete")

    @property
    def is_alive(self):
        return self._thread is not None and self._thread.is_alive()

    @property
    def status(self):
        return {
            "alive": self.is_alive,
            "pulse_count": self._pulse_count,
            "jobs_registered": self._jobs_registered,
            "pending_jobs": len(schedule.get_jobs()),
        }


# Singleton instance
heartbeat = HeartbeatScheduler()
