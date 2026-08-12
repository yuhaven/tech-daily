"""Generate a self-contained static index.html from the collected JSON snapshots."""

import html
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import common

sys.path.insert(0, str(Path(__file__).resolve().parent))

BJ_TZ = timezone(timedelta(hours=8))
SITE_NAME = "Daily Tech Pulse"
SITE_CN = "每日技术情报"

LANG_COLORS = {
    "Python": "#3572A5",
    "TypeScript": "#3178c6",
    "JavaScript": "#f1e05a",
    "Rust": "#dea584",
    "Go": "#00ADD8",
    "C++": "#f34b7d",
    "C": "#555555",
    "C#": "#178600",
    "Java": "#b07219",
    "Swift": "#F05138",
    "Kotlin": "#A97BFF",
    "Ruby": "#701516",
    "PHP": "#4F5D95",
    "Shell": "#89e051",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Vue": "#41b883",
    "Svelte": "#ff3e00",
    "Solidity": "#AA6746",
    "Zig": "#ec915c",
}


def esc(text):
    return html.escape(str(text or ""), quote=True)


def fmt_bj(ts):
    if not ts:
        return ""
    return datetime.fromtimestamp(ts, BJ_TZ).strftime("%Y-%m-%d %H:%M")


def parse_iso(iso):
    if not iso:
        return 0
    try:
        return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp())
    except (ValueError, TypeError):
        return 0


def rel_time(ts):
    if not ts:
        return ""
    diff = max(0, int(datetime.now(BJ_TZ).timestamp()) - int(ts))
    if diff < 60:
        return "刚刚"
    if diff < 3600:
        return f"{diff // 60} 分钟前"
    if diff < 86400:
        return f"{diff // 3600} 小时前"
    if diff < 86400 * 7:
        return f"{diff // 86400} 天前"
    return fmt_bj(ts)


def lang_color(lang):
    return LANG_COLORS.get(lang or "", "#9aa4b2")


def empty_state(text="该数据源暂无可展示内容，请稍后再来"):
    return f'<div class="empty">{esc(text)}</div>'


def repo_card(idx, repo):
    name = esc(repo["full_name"])
    desc = esc(repo.get("description")) or "暂无描述"
    url = f"https://github.com{esc(repo['url'])}"
    lang_html = ""
    if repo.get("language"):
        lang_html = (
            f'<span class="lang"><span class="dot" '
            f'style="background:{lang_color(repo["language"])}"></span>'
            f'{esc(repo["language"])}</span>'
        )
    today_html = ""
    if repo.get("stars_today"):
        today_html = f'<span class="stars-today">▲ {repo["stars_today"]:,} 今日新增</span>'
    total_html = ""
    if repo.get("stars_total"):
        total_html = f'<span class="stars-total">⭐ {repo["stars_total"]:,}</span>'
    return (
        f'<a class="repo-card" href="{url}" target="_blank" rel="noopener" draggable="false">'
        f'<span class="rank">{idx}</span>'
        f'<span class="repo-main">'
        f'<span class="repo-name">{name}</span>'
        f'<span class="repo-desc">{desc}</span>'
        f'<span class="repo-meta">{lang_html}{today_html}{total_html}</span>'
        f"</span></a>"
    )


def build_github(github):
    periods = (("daily", "今日"), ("weekly", "本周"), ("monthly", "本月"))
    tabs = "".join(
        f'<button class="tab-btn{" active" if key == "daily" else ""}" '
        f'data-period="{key}">{label}</button>'
        for key, label in periods
    )
    lists = ""
    for key, _ in periods:
        repos = github.get("data", {}).get(key, [])
        rows = "".join(repo_card(i, r) for i, r in enumerate(repos[:12], 1))
        lists += (
            f'<div class="gh-list{" active" if key == "daily" else ""}" '
            f'data-period="{key}">{rows or empty_state()}</div>'
        )
    return f"""
<section id="github">
  <div class="sec-head">
    <span class="badge gh">★</span><h2>GitHub Star 排行榜</h2>
    <span class="sec-note">按期间新增 Star 排序 · 来源 GitHub Trending</span>
  </div>
  <div class="tabs">{tabs}</div>
  {lists}
</section>"""


def hn_item(item):
    points = item.get("points", 0)
    comments = item.get("comments", 0)
    meta = (
        f"{esc(item.get('domain', 'news.ycombinator.com'))} · "
        f"{rel_time(item.get('time'))} · 💬 {comments}"
    )
    return (
        f'<a class="news-item" href="{esc(item["url"])}" target="_blank" rel="noopener" draggable="false">'
        f'<span class="heat">{points}</span>'
        f'<span class="news-main">'
        f'<span class="news-title">{esc(item["title"])}</span>'
        f'<span class="news-meta">{meta}</span>'
        f"</span></a>"
    )


def media_item(item):
    snippet = esc(item.get("snippet")) or ""
    snippet_html = (
        f'<span class="news-snippet">{snippet}</span>' if snippet else ""
    )
    meta = (
        f'<span class="source-pill">{esc(item.get("source", ""))}</span>'
        f" {rel_time(item.get('time'))}"
    )
    return (
        f'<a class="news-item" href="{esc(item["url"])}" target="_blank" rel="noopener" draggable="false">'
        f'<span class="heat media">媒体</span>'
        f'<span class="news-main">'
        f'<span class="news-title">{esc(item["title"])}</span>'
        f'{snippet_html}'
        f'<span class="news-meta">{meta}</span>'
        f"</span></a>"
    )


def build_news(news):
    hn = news.get("hn", [])
    media = news.get("media", [])
    hn_rows = "".join(hn_item(x) for x in hn[:12]) or empty_state()
    media_rows = "".join(media_item(x) for x in media[:10]) or empty_state()
    return f"""
<section id="news">
  <div class="sec-head">
    <span class="badge ai">AI</span><h2>AI 前沿新闻</h2>
    <span class="sec-note">按真实热度排序 · Hacker News 投票 + 欧美主流科技媒体</span>
  </div>
  <div class="grid2">
    <div>
      <div class="col-title"><span class="pill">HOT</span>HN 热度榜（AI 相关）</div>
      {hn_rows}
    </div>
    <div>
      <div class="col-title"><span class="pill">MEDIA</span>媒体最新动态</div>
      {media_rows}
    </div>
  </div>
</section>"""


def tool_item(item, tag):
    points = item.get("points", 0)
    meta = (
        f"{esc(item.get('domain', 'news.ycombinator.com'))} · "
        f"{rel_time(parse_iso(item.get('time')))} · 💬 {item.get('comments', 0)}"
    )
    return (
        f'<a class="news-item" href="{esc(item["url"])}" target="_blank" rel="noopener" draggable="false">'
        f'<span class="heat">{points}</span>'
        f'<span class="news-main">'
        f'<span class="news-title">{esc(item["title"])}</span>'
        f'<span class="news-meta">{meta}</span>'
        f"</span></a>"
    )


def build_tools(tools):
    showhn = tools.get("showhn", [])
    hot = tools.get("hot", [])
    show_rows = "".join(tool_item(x, "NEW") for x in showhn[:12]) or empty_state()
    hot_rows = "".join(tool_item(x, "HOT") for x in hot[:12]) or empty_state()
    return f"""
<section id="tools">
  <div class="sec-head">
    <span class="badge tools">⚙</span><h2>最新技术 & 工具</h2>
    <span class="sec-note">开发者真实发布的新工具与高分技术讨论 · 来源 Hacker News</span>
  </div>
  <div class="grid2">
    <div>
      <div class="col-title"><span class="pill">SHOW HN</span>新工具发布</div>
      {show_rows}
    </div>
    <div>
      <div class="col-title"><span class="pill">HOT</span>本周技术热点</div>
      {hot_rows}
    </div>
  </div>
</section>"""


CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; user-select: text; -webkit-user-select: text; }
:root {
  --bg: #2b2b2b; --card: #313335; --border: #46494d;
  --text: #a9b7c6; --heading: #e8e8e8; --muted: #7f8b98;
  --orange: #cc7832; --blue: #6897bb; --green: #6a8759;
  --yellow: #e8bf6a; --sel: #214283; --radius: 8px;
}
html { scroll-behavior: smooth; }
a, a * { -webkit-user-drag: none; user-drag: none; }
body {
  background: var(--bg); color: var(--text); line-height: 1.45;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
    "Hiragino Sans GB", "Microsoft YaHei", "JetBrains Mono", "Helvetica Neue", Arial, sans-serif;
}
::selection { background: var(--sel); color: #fff; }
.container { max-width: 1080px; margin: 0 auto; padding: 0 16px; }
.topnav {
  position: sticky; top: 0; z-index: 100;
  background: rgba(47, 49, 51, .96); backdrop-filter: blur(6px);
  border-bottom: 1px solid var(--border);
}
.nav-inner { display: flex; align-items: center; justify-content: space-between; height: 44px; }
.brand { font-weight: 700; font-size: 14px; color: var(--heading); }
.brand .cn { color: var(--muted); font-weight: 600; margin-left: 6px; font-size: 12px; }
.nav-links { display: flex; gap: 16px; font-size: 12.5px; }
.nav-links a { color: var(--muted); text-decoration: none; }
.nav-links a:hover { color: var(--yellow); }
header.hero {
  background: linear-gradient(180deg, #313335, #2b2b2b);
  border-bottom: 1px solid var(--border); padding: 16px 0 12px;
}
.hero h1 { font-size: 20px; letter-spacing: -0.01em; color: var(--heading); }
.hero h1 .cn { font-size: 14px; color: var(--muted); font-weight: 600; margin-left: 8px; }
.hero .sub { color: var(--muted); margin-top: 4px; font-size: 12.5px; }
.hero .meta { margin-top: 8px; font-size: 11.5px; color: #6b7681; }
main.container { padding-bottom: 28px; }
section { margin-top: 24px; scroll-margin-top: 56px; }
.sec-head { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 10px; }
.sec-head h2 { font-size: 16.5px; color: var(--heading); }
.badge {
  display: inline-flex; align-items: center; justify-content: center;
  width: 24px; height: 24px; border-radius: 6px; font-size: 13px;
}
.badge.gh { background: #3d3530; color: var(--orange); }
.badge.ai { background: #2f3a45; color: var(--blue); }
.badge.tools { background: #2f3f38; color: var(--green); }
.sec-note { font-size: 11px; color: var(--muted); }
.tabs { display: flex; gap: 6px; margin-bottom: 10px; }
.tab-btn {
  border: 1px solid var(--border); background: var(--card); color: var(--muted);
  padding: 4px 14px; border-radius: 999px; font-size: 12.5px; cursor: pointer;
  transition: all .15s ease; font-family: inherit;
}
.tab-btn:hover { border-color: var(--orange); color: var(--orange); }
.tab-btn.active { background: var(--orange); border-color: var(--orange); color: #1c1c1c; font-weight: 600; }
.gh-list { display: none; }
.gh-list.active { display: block; }
.repo-card {
  display: flex; gap: 12px; align-items: flex-start; background: var(--card);
  border: 1px solid var(--border); border-radius: var(--radius);
  padding: 8px 12px; margin-bottom: 6px; text-decoration: none; color: inherit;
  transition: border-color .15s ease, background .15s ease;
}
.repo-card:hover { border-color: var(--orange); background: #36383b; }
.rank {
  font-size: 14px; font-weight: 700; color: #5f6a75; min-width: 22px;
  text-align: center; font-variant-numeric: tabular-nums; padding-top: 1px;
}
.repo-card:nth-child(-n+3) .rank { color: var(--orange); }
.repo-main { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.repo-name {
  font-weight: 700; font-size: 13px;
  font-family: ui-monospace, "JetBrains Mono", "SF Mono", Consolas, "Cascadia Mono", monospace;
  color: var(--blue);
}
.repo-card:hover .repo-name { color: #7db3da; }
.repo-desc {
  color: #98a4b0; font-size: 12px; overflow-wrap: break-word;
  display: -webkit-box; -webkit-line-clamp: 1; -webkit-box-orient: vertical; overflow: hidden;
}
.repo-meta { display: flex; gap: 10px; font-size: 11.5px; color: var(--muted); align-items: center; flex-wrap: wrap; }
.lang { display: inline-flex; align-items: center; gap: 5px; }
.dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.stars-today { color: var(--yellow); font-weight: 600; }
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.col-title { font-size: 12.5px; font-weight: 700; color: var(--muted); margin-bottom: 8px; display: flex; align-items: center; gap: 6px; }
.col-title .pill { background: #3a3c3f; color: var(--yellow); font-size: 10.5px; padding: 1px 7px; border-radius: 999px; letter-spacing: .03em; }
.news-item {
  display: flex; gap: 9px; background: var(--card); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 7px 10px; margin-bottom: 5px; text-decoration: none;
  color: inherit; transition: border-color .15s ease, background .15s ease; align-items: flex-start;
}
.news-item:hover { border-color: var(--blue); background: #36383b; }
.heat {
  background: var(--orange); color: #1c1c1c; font-size: 11px; font-weight: 700;
  border-radius: 6px; padding: 3px 7px; min-width: 38px; text-align: center;
  flex-shrink: 0; font-variant-numeric: tabular-nums; margin-top: 1px;
}
.heat.media { background: #3a3c3f; color: var(--blue); font-size: 10.5px; }
.news-main { min-width: 0; display: flex; flex-direction: column; gap: 1px; }
.news-title { font-size: 13px; font-weight: 600; line-height: 1.35; color: var(--text); }
.news-item:hover .news-title { color: var(--yellow); }
.news-meta { font-size: 11.5px; color: var(--muted); display: flex; gap: 5px; align-items: center; flex-wrap: wrap; }
.news-snippet {
  font-size: 11.5px; color: #6b7681;
  display: -webkit-box; -webkit-line-clamp: 1; -webkit-box-orient: vertical; overflow: hidden;
}
.source-pill { background: #3a3c3f; color: var(--green); font-size: 10.5px; padding: 1px 6px; border-radius: 4px; }
.empty {
  background: var(--card); border: 1px dashed var(--border); color: var(--muted);
  border-radius: var(--radius); padding: 14px; text-align: center; font-size: 12px;
}
footer { border-top: 1px solid var(--border); background: #2f3133; padding: 14px 0; margin-top: 24px; }
.foot { font-size: 11.5px; color: var(--muted); display: flex; flex-direction: column; gap: 3px; }
.foot a { color: var(--blue); text-decoration: none; }
.foot a:hover { color: var(--yellow); }
@media (max-width: 820px) {
  .grid2 { grid-template-columns: 1fr; }
  .hero h1 { font-size: 17px; }
  .brand .cn { display: none; }
}
"""


SCRIPT = """
document.querySelectorAll('.tab-btn').forEach(function (btn) {
  btn.addEventListener('click', function () {
    var period = btn.dataset.period;
    document.querySelectorAll('.tab-btn').forEach(function (b) {
      b.classList.toggle('active', b === btn);
    });
    document.querySelectorAll('.gh-list').forEach(function (list) {
      list.classList.toggle('active', list.dataset.period === period);
    });
  });
});
"""


def build_page(github, news, tools):
    generated = parse_iso(github.get("generated_at") or news.get("generated_at") or tools.get("generated_at") or "")
    updated = fmt_bj(generated) or "—"
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark">
<title>{SITE_NAME} · {SITE_CN}</title>
<style>{CSS}</style>
</head>
<body>
<div id="top"></div>
<nav class="topnav">
  <div class="container nav-inner">
    <span class="brand">{SITE_NAME}<span class="cn">{SITE_CN}</span></span>
    <span class="nav-links">
      <a href="#github">GitHub 排行榜</a>
      <a href="#news">AI 新闻</a>
      <a href="#tools">工具</a>
    </span>
  </div>
</nav>
<header class="hero">
  <div class="container">
    <h1>{SITE_NAME}<span class="cn">{SITE_CN}</span></h1>
    <p class="sub">GitHub 趋势 · AI 前沿 · 最新工具 —— 聚合欧美真实公开数据，每天自动更新</p>
    <p class="meta">数据更新于 {esc(updated)}（UTC+8） · 来源：GitHub Trending / Hacker News / 五大欧美科技媒体</p>
  </div>
</header>
<main class="container">
  {build_github(github)}
  {build_news(news)}
  {build_tools(tools)}
</main>
<footer>
  <div class="container foot">
    <span>{SITE_NAME} · 每日自动生成，内容为公开数据聚合，仅供信息参考；点击条目可跳转原文。</span>
    <span>生成时间：{esc(updated)}（UTC+8）</span>
    <span><a href="#top">回到顶部 ↑</a></span>
  </div>
</footer>
<script>{SCRIPT}</script>
</body>
</html>"""


def main():
    github = common.read_json(common.DATA / "github_trending.json")
    news = common.read_json(common.DATA / "ai_news.json")
    tools = common.read_json(common.DATA / "tools.json")
    page = build_page(github, news, tools)
    out = common.ROOT / "index.html"
    out.write_text(page, encoding="utf-8")
    print(f"[site] wrote {out} ({len(page)} bytes)")


if __name__ == "__main__":
    main()
