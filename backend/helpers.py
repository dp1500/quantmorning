"""
helpers.py — Shared utilities for all backend modules.
"""
from __future__ import annotations
import json
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from functools import wraps
from typing import Any, Callable

import pandas as pd

import math

IST = timezone(timedelta(hours=5, minutes=30))


def _sanitize(obj: Any) -> Any:
    """Recursively replace NaN/Infinity with 0 for JSON safety."""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return 0.0
        return obj
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize(v) for v in obj]
    return obj


class RateLimiter:
    """Simple rate limiter respecting requests/min threshold."""
    def __init__(self, max_calls_per_minute: int = 99):
        self.min_interval = 60.0 / max_calls_per_minute
        self._last_call = 0.0

    def wait(self):
        now = time.monotonic()
        elapsed = now - self._last_call
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self._last_call = time.monotonic()

    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            self.wait()
            return func(*args, **kwargs)
        return wrapper


def get_upstox_client(access_token: str):
    """Create and return a configured Upstox ApiClient."""
    import upstox_client
    config = upstox_client.Configuration()
    config.access_token = access_token
    return upstox_client.ApiClient(config)


def ist_now() -> datetime:
    return datetime.now(IST)


def ist_today_str() -> str:
    return ist_now().strftime("%Y-%m-%d")


def write_json(data: Any, path: Path, pretty: bool = True):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = _sanitize(data)  # kill NaN/Inf before serializing
    with open(path, "w") as f:
        json.dump(data, f, indent=2 if pretty else None, default=str, ensure_ascii=False)
    print(f"  ✓ Wrote {path.name} ({path.stat().st_size:,} bytes)")


def write_json_dual(data: Any, final_dir: Path, frontend_dir: Path, filename: str):
    """Write same JSON to both final_data/ and src/data/."""
    write_json(data, final_dir / filename)
    write_json(data, frontend_dir / filename)


def safe_float(val, default=0.0) -> float:
    try:
        v = float(val)
        return default if math.isnan(v) or math.isinf(v) else v
    except (TypeError, ValueError):
        return default


def safe_int(val, default=0) -> int:
    try:
        v = int(float(val))
        return default if math.isnan(float(val)) else v
    except (TypeError, ValueError):
        return default
