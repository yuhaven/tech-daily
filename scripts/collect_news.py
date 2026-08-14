"""Collect AI news: Hacker News top stories (points = heat) + major media RSS."""

import re
import sys
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlparse

import common

sys.path.insert(0, str(Path(__file__).resolve().parent))

HN_TOP_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"
HN_DISCUSS = "https://news.ycombinator.com/item?id={}"
TOP_STORY_LIMIT = 120
TOP_AI_RESULTS = 12

FEEDS = [
    ("TechCrunch", "https://techcrunch.com/category/artificial-intelligence/feed/"),
    ("VentureBeat", "https://venturebeat.com/category/ai/feed/"),
    ("The Verge", "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"),
    ("MIT Tech Review", "https://www.technologyreview.com/topic/artificial-intelligence/feed"),
    ("Ars Technica", "https://feeds.arstechnica.com/arstechnica/index"),
]
MEDIA_PER_SOURCE = 4
MEDIA_TOTAL = 10

AI_KEYWORDS = [
    r"\bai\b",
    r"artificial intelligence",
    r"openai",
    r"anthropic",
    r"claude",
    r"gpt-?\d?",
    r"\bllm\b",
    r"large language model",
    r"language model",
    r"machine learning",
    r"deep learning",
    r"neural network",
    r"foundation model",
    r"gemini",
    r"deepmind",
    r"transformer",
    r"agent(s)?\b",
    r"chatbot",
    r"stable diffusion",
    r"diffusion model",
    r"computer vision",
    r"\bnlp\b",
    r"natural language",
    r"\brag\b",
    r"fine-?tun",
    r"generative",
    r"copilot",
    r"mistral",
    r"llama",
    r"multimodal",
    r"inference",
    r"\bgpu\b",
    r"nvidia",
    r"hallucinat",
    r"embedding",
    r"vector database",
    r"augmented generation",
]
AI_RE = re.compile("|".join(f"(?:{k})" for k in AI_KEYWORDS), re.I)


def is_ai(text):
    return bool(AI_RE.search(text or ""))


def fetch_hit(item_id):
    try:
        return common.fetch_json(HN_ITEM_URL.format(item_id))
    except Exception:  # noqa: BLE001
        return None


def collect_hn_ai():
    try:
        ids = common.fetch_json(HN_TOP_URL)[:TOP_STORY_LIMIT]
    except Exception as exc:  # noqa: BLE001
        print(f"[news] HN top stories failed: {exc}")
        return []
    items = []
    with ThreadPoolExecutor(max_workers=10) as pool:
        raw = list(pool.map(fetch_hit, ids))
    for item in raw:
        if not item or item.get("type") != "story":
            continue
        title = (item.get("title") or "").strip()
        if not title or not is_ai(title):
            continue
        url = item.get("url") or HN_DISCUSS.format(item["id"])
        domain = ""
        try:
            domain = urlparse(url).netloc.removeprefix("www.")
        except ValueError:
            pass
        items.append(
            {
                "id": item["id"],
                "title": title,
                "url": url,
                "domain": domain or "news.ycombinator.com",
                "points": item.get("score") or 0,
                "comments": item.get("descendants") or 0,
                "author": item.get("by") or "",
                "time": item.get("time") or 0,
            }
        )
    items.sort(key=lambda x: x["points"], reverse=True)
    return items[:TOP_AI_RESULTS]


def strip_html(text):
    text = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", text).strip()


def parse_feed(name, feed_url):
    try:
        xml_text = common.http_text(feed_url)
        root = ET.fromstring(xml_text)
    except Exception as exc:  # noqa: BLE001
        print(f"[news] feed {name} failed: {exc}")
        return []
    items = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        if not title or not link:
            continue
        if name == "Ars Technica" and not is_ai(title):
            continue
        pub = (item.findtext("pubDate") or "").strip()
        ts = 0
        try:
            ts = int(parsedate_to_datetime(pub).timestamp())
        except (TypeError, ValueError):
            pass
        items.append(
            {
                "title": title,
                "url": link,
                "source": name,
                "published": pub,
                "time": ts,
                "snippet": strip_html(item.findtext("description") or "")[:180],
            }
        )
    return items[:MEDIA_PER_SOURCE]


def collect_media():
    all_items = []
    seen = set()
    for name, url in FEEDS:
        for item in parse_feed(name, url):
            if item["url"] in seen:
                continue
            seen.add(item["url"])
            all_items.append(item)
    all_items.sort(key=lambda x: x["time"], reverse=True)
    return all_items[:MEDIA_TOTAL]


def main():
    hn = collect_hn_ai()
    print(f"[news] HN AI stories: {len(hn)}")
    media = collect_media()
    print(f"[news] media stories: {len(media)}")

    # Reuse translations from the previous run when titles are unchanged.
    previous = common.read_json(common.DATA / "ai_news.json")
    cache = {}
    for item in previous.get("hn", []) + previous.get("media", []):
        title = item.get("title")
        zh = item.get("title_zh")
        if title and zh:
            cache[title] = zh

    translated = 0
    for item in hn + media:
        title = item.get("title")
        if not title:
            item["title_zh"] = None
            continue
        if title in cache:
            item["title_zh"] = cache[title]
            continue
        zh = common.translate(title)
        cache[title] = zh
        item["title_zh"] = zh
        if zh:
            translated += 1
    print(f"[news] translated: {translated}")

    common.write_json(
        common.DATA / "ai_news.json",
        {
            "generated_at": common.now_iso(),
            "hn": hn,
            "media": media,
        },
    )


if __name__ == "__main__":
    main()
