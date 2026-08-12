"""Shared helpers: HTTP fetching, JSON I/O, star-count parsing."""

import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 DailyTechPulse/1.0"
)
TIMEOUT = 30


def http_get(url, timeout=TIMEOUT):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json,text/html,application/rss+xml,*/*",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def http_text(url, timeout=TIMEOUT):
    data = http_get(url, timeout)
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def fetch_json(url, timeout=TIMEOUT):
    return json.loads(http_get(url, timeout).decode("utf-8"))


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path, default=None):
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8"))


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def parse_stars(text):
    """Parse strings like '1,234', '12.3k', '1.2m' into an integer or None."""
    if not text:
        return None
    m = re.search(r"([\d,]+(?:\.\d+)?)\s*([km]?)", text, re.I)
    if not m:
        return None
    num = float(m.group(1).replace(",", ""))
    unit = m.group(2).lower()
    if unit == "k":
        num *= 1_000
    elif unit == "m":
        num *= 1_000_000
    return int(num)
