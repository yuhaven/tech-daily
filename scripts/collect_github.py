"""Fetch GitHub Trending (daily/weekly/monthly), with Search API fallback."""

import sys
from datetime import date, timedelta
from html.parser import HTMLParser
from pathlib import Path

import common

sys.path.insert(0, str(Path(__file__).resolve().parent))

TRENDING_URL = "https://github.com/trending?since={period}"
PERIODS = (("daily", 1), ("weekly", 7), ("monthly", 30))
MAX_ITEMS = 12


class TrendingParser(HTMLParser):
    """Extract repo cards from the github.com/trending HTML page."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.repos = []
        self.cur = None
        self.in_h2 = False
        self.in_h2_link = False
        self.in_desc = False
        self.in_lang = False
        self.in_today = False
        self.in_total = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get("class", "")
        if tag == "article" and "Box-row" in cls:
            self.cur = {
                "full_name": "",
                "url": "",
                "description": "",
                "language": None,
                "stars_today": None,
                "stars_total": None,
                "_today_raw": "",
                "_total_raw": "",
            }
            return
        if self.cur is None:
            return
        if tag == "h2":
            self.in_h2 = True
        elif tag == "a" and self.in_h2:
            href = a.get("href", "")
            if href.startswith("/") and href.count("/") == 2:
                self.cur["url"] = href
                self.cur["full_name"] = href.strip("/")
                self.in_h2_link = True
        elif tag == "p" and "col-9" in cls:
            self.in_desc = True
        elif tag == "span" and a.get("itemprop") == "programmingLanguage":
            self.in_lang = True
        elif tag == "span" and "float-sm-right" in cls:
            self.in_today = True
        elif tag == "a" and a.get("href", "").endswith("/stargazers"):
            self.in_total = True

    def handle_data(self, data):
        if self.cur is None:
            return
        if self.in_desc:
            self.cur["description"] += data
        elif self.in_lang:
            self.cur["language"] = (self.cur["language"] or "") + data
        elif self.in_today:
            self.cur["_today_raw"] += data
        elif self.in_total:
            self.cur["_total_raw"] += data

    def handle_endtag(self, tag):
        if tag == "article" and self.cur is not None:
            c = self.cur
            c["description"] = _clean(c["description"])
            c["language"] = _clean(c["language"]) or None
            c["stars_today"] = common.parse_stars(c["_today_raw"])
            c["stars_total"] = common.parse_stars(c["_total_raw"])
            c.pop("_today_raw", None)
            c.pop("_total_raw", None)
            if c["full_name"]:
                self.repos.append(c)
            self.cur = None
            self.in_h2 = self.in_h2_link = self.in_desc = self.in_lang = False
            self.in_today = self.in_total = False
            return
        if self.cur is None:
            return
        if tag == "h2":
            self.in_h2 = False
        elif tag == "a":
            self.in_h2_link = False
            self.in_total = False
        elif tag == "p":
            self.in_desc = False
        elif tag == "span":
            self.in_lang = False
            self.in_today = False


def _clean(text):
    import re

    return re.sub(r"\s+", " ", text or "").strip()


def search_fallback(days):
    """Official Search API fallback: repos created in the period, sorted by stars."""
    since = (date.today() - timedelta(days=days)).isoformat()
    url = (
        "https://api.github.com/search/repositories"
        f"?q=created:>{since}&sort=stars&order=desc&per_page={MAX_ITEMS}"
    )
    data = common.fetch_json(url)
    items = []
    for r in data.get("items", []):
        items.append(
            {
                "full_name": r["full_name"],
                "url": "/" + r["full_name"],
                "description": r.get("description") or "",
                "language": r.get("language"),
                "stars_today": None,
                "stars_total": r.get("stargazers_count"),
            }
        )
    return items


def collect_period(period, days):
    try:
        html = common.http_text(TRENDING_URL.format(period=period))
        parser = TrendingParser()
        parser.feed(html)
        repos = parser.repos[:MAX_ITEMS]
        if not repos:
            raise ValueError("no repo cards parsed")
        return repos
    except Exception as exc:  # noqa: BLE001 - deliberate global fallback
        print(f"[github] {period} trending failed ({exc}); using Search API fallback")
        return search_fallback(days)


def main():
    result = {}
    # Reuse translations from the previous run when descriptions are unchanged.
    previous = common.read_json(common.DATA / "github_trending.json")
    cache = {}
    for period_repos in previous.get("data", {}).values():
        for repo in period_repos:
            desc = repo.get("description")
            zh = repo.get("description_zh")
            if desc and zh:
                cache[desc] = zh

    translated = 0
    skipped = 0
    for period, days in PERIODS:
        repos = collect_period(period, days)
        for repo in repos:
            desc = repo.get("description")
            if not desc:
                repo["description_zh"] = None
                skipped += 1
                continue
            if desc in cache:
                repo["description_zh"] = cache[desc]
                skipped += 1
                continue
            zh = common.translate(desc)
            cache[desc] = zh
            repo["description_zh"] = zh
            if zh:
                translated += 1
            else:
                skipped += 1
        result[period] = repos
        print(f"[github] {period}: {len(repos)} repos")
    print(f"[github] translated: {translated}, cached/failed: {skipped}")
    common.write_json(
        common.DATA / "github_trending.json",
        {"generated_at": common.now_iso(), "data": result},
    )


if __name__ == "__main__":
    main()
