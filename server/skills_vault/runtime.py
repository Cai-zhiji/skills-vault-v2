from __future__ import annotations

import ctypes
import os
import secrets
import signal
import sys
import threading
import time
from typing import Callable, Optional


def session_token() -> str:
    return secrets.token_urlsafe(32)


def startup_id() -> str:
    return secrets.token_hex(16)


def parent_is_alive(parent_pid: int) -> bool:
    if parent_pid <= 0:
        return False
    if sys.platform == "win32":
        process_query_limited_information = 0x1000
        synchronize = 0x00100000
        handle = ctypes.windll.kernel32.OpenProcess(  # type: ignore[attr-defined]
            process_query_limited_information | synchronize,
            False,
            parent_pid,
        )
        if not handle:
            return False
        try:
            wait_timeout = 0x00000102
            return ctypes.windll.kernel32.WaitForSingleObject(handle, 0) == wait_timeout  # type: ignore[attr-defined]
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)  # type: ignore[attr-defined]
    try:
        os.kill(parent_pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def start_parent_monitor(
    parent_pid: Optional[int],
    shutdown: Callable[[], None],
    interval_seconds: float = 2.0,
) -> Optional[threading.Thread]:
    if not parent_pid:
        return None

    def monitor() -> None:
        while parent_is_alive(parent_pid):
            time.sleep(interval_seconds)
        shutdown()

    thread = threading.Thread(target=monitor, name="parent-monitor", daemon=True)
    thread.start()
    return thread
