"""Logging helpers."""

import logging
import threading
import time

# Minimum seconds between emails for the same error (per process).
THROTTLE_SECONDS = 10 * 60


class ThrottleFilter(logging.Filter):
    """Allow each distinct error through at most once per THROTTLE_SECONDS."""

    _lock = threading.Lock()
    _last_sent: dict = {}

    @classmethod
    def reset(cls):
        with cls._lock:
            cls._last_sent.clear()

    def filter(self, record):
        if record.exc_info and record.exc_info[0] is not None:
            key = (record.exc_info[0].__name__, str(record.exc_info[1]))
        else:
            key = (record.name, record.getMessage())
        now = time.monotonic()
        with self._lock:
            last = self._last_sent.get(key)
            if last is not None and now - last < THROTTLE_SECONDS:
                return False
            self._last_sent[key] = now
        return True
