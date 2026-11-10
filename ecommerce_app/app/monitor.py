import time
from collections import deque
from threading import Lock


class RequestMonitor:
    """In-memory counters for the running process.

    These reset when the process stops. They are enough to watch a local or
    Codio run without sending data to an outside monitoring service.
    """

    def __init__(self):
        self.started_at = time.time()
        self.requests = 0
        self.client_errors = 0
        self.server_errors = 0
        self.failed_logins = 0
        self.recent = deque(maxlen=15)
        self._lock = Lock()

    def record(self, method, path, status_code, duration_ms):
        with self._lock:
            self.requests += 1
            if 400 <= status_code < 500:
                self.client_errors += 1
            elif status_code >= 500:
                self.server_errors += 1
            self.recent.appendleft(
                {
                    "method": method,
                    "path": path,
                    "status": status_code,
                    "duration_ms": round(duration_ms, 1),
                }
            )

    def record_failed_login(self):
        with self._lock:
            self.failed_logins += 1

    def snapshot(self):
        with self._lock:
            return {
                "uptime_seconds": int(time.time() - self.started_at),
                "requests": self.requests,
                "client_errors": self.client_errors,
                "server_errors": self.server_errors,
                "failed_logins": self.failed_logins,
                "recent": list(self.recent),
                "alert": self.failed_logins >= 3,
            }
