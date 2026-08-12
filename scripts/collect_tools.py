"""Collect latest tools: Hacker News Show HN + high-scoring tech stories."""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

import common

sys.path.insert(0, str(Path(__file__).resolve().parent))


def _recent_epoch(days=30):
    return int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp())


SHOW_HN_URL = (
    "https://hn.algolia.com/api/v1/search?tags=show_hn&hitsPerPage=100"
    f"&numericFilters=created_at_i>{_recent_epoch()}"
)
HOT_URL = (
    "https://hn.algolia.com/api/v1/search?tags=story&hitsPerPage=100"
    f"&numericFilters=points>100,created_at_i>{_recent_epoch()}"
)
TOP_N = 12


def to_items(hits):
    items = []
    for h in hits:
        title = (h.get("title") or "").strip()
        if not title:
            continue
        url = h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}"
        domain = ""
        try:
            domain = urlparse(url).netloc.removeprefix("www.")
        except ValueError:
            pass
        created = h.get("created_at") or ""
        items.append(
            {
                "title": title,
                "url": url,
                "domain": domain or "news.ycombinator.com",
                "points": h.get("points") or 0,
                "comments": h.get("num_comments") or 0,
                "author": h.get("author") or "",
                "time": created,
            }
        )
    items.sort(key=lambda x: x["points"], reverse=True)
    return items[:TOP_N]


def collect_show_hn():
    try:
        data = common.fetch_json(SHOW_HN_URL)
        return to_items(data.get("hits", []))
    except Exception as exc:  # noqa: BLE001
        print(f"[tools] Show HN failed: {exc}")
        return []


def collect_hot():
    try:
        data = common.fetch_json(HOT_URL)
        return to_items(data.get("hits", []))
    except Exception as exc:  # noqa: BLE001
        print(f"[tools] hot stories failed: {exc}")
        return []


def main():
    showhn = collect_show_hn()
    hot = collect_hot()
    print(f"[tools] Show HN: {len(showhn)}, hot stories: {len(hot)}")
    common.write_json(
        common.DATA / "tools.json",
        {
            "generated_at": common.now_iso(),
            "showhn": showhn,
            "hot": hot,
        },
    )


if __name__ == "__main__":
    main()
