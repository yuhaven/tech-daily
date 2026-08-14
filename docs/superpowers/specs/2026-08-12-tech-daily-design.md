# Daily Tech Pulse（每日技术情报站）设计文档

日期：2026-08-12

## 1. 目标

构建一个每天自动更新的静态网页，聚合三类真实、有热度的信息：

1. **GitHub Star 排行榜**：每日 / 每周 / 每月新增 star 最多的仓库。
2. **AI 前沿新闻**：按真实热度（Hacker News 用户投票分数）排序的 AI 新闻，辅以欧美主流科技媒体的最新报道。
3. **最新技术 & 工具**：开发者社区中真实发布、有热度的高分新工具与技术动态。

信息以欧美前沿动态为主，内容保持英文原文（标题不翻译），页面框架使用中文；GitHub 仓库描述附一行机器翻译的中文参考（带“译：”前缀），原文保持权威。

## 2. 架构

纯 Python 标准库实现（零第三方依赖），GitHub Actions 定时运行，产出静态 HTML 部署到 GitHub Pages。

```text
collect_github.py  ─┐
collect_news.py    ─┼─▶ data/*.json ──▶ generate_site.py ──▶ index.html ──▶ GitHub Pages
collect_tools.py   ─┘      (每日快照)          │
                                              └─ 含更新时间戳
```

### 组件职责

| 组件 | 职责 | 依赖 |
|---|---|---|
| `collect_github.py` | 抓取 GitHub Trending（daily/weekly/monthly），输出 JSON | urllib + html.parser（标准库） |
| `collect_news.py` | 聚合 Hacker News 高分 AI 新闻 + 主流媒体 RSS | urllib + xml.etree（标准库） |
| `collect_tools.py` | 抓取 Hacker News Show HN 高分新工具 + 技术热点 | urllib + json（标准库） |
| `generate_site.py` | 读取 data/*.json，生成自包含单文件 index.html | json（标准库） |
| `.github/workflows/daily.yml` | 每天定时采集、构建、部署 Pages | GitHub Actions 内置 runner |

## 3. 数据源

| 板块 | 来源 | 热度/真实性依据 | 降级方案 |
|---|---|---|---|
| GitHub 排行榜 | `github.com/trending?since=daily/weekly/monthly` | GitHub 官方按期间新增 star 排序 | GitHub Search API（按期间创建 + star 排序） |
| AI 新闻（热度榜） | Hacker News API（topstories + item，AI 关键词过滤，按 points 排序） | 真实用户投票分数 | 仅展示 RSS 源 |
| AI 新闻（最新动态） | TechCrunch AI / VentureBeat AI / The Verge AI / MIT Technology Review AI / Ars Technica 官方 RSS | 官方发布源 | 逐源容错，失败源跳过 |
| 最新工具 | Hacker News "Show HN"（Algolia API，按分数排序） | 开发者亲手发布 + 真实投票 | 跳过该板块 |
| 技术热点 | HN 高分技术帖（points > 100） | 真实投票热度 | 跳过该板块 |

所有请求携带浏览器风格 User-Agent；Hacker News API 免费无需 Key。

## 4. 页面设计

- 单页三段式布局，中文界面框架，内容标题保持英文原文。
- 顶部：站名、数据更新时间、数据来源说明。
- 板块一：GitHub Star 排行榜，Daily / Weekly / Monthly 标签切换，显示排名、仓库名、语言、描述、期间新增 star。
- 板块二：AI 前沿新闻，分"HN 热度榜"与"媒体最新"两栏。
- 板块三：最新技术 & 工具，Show HN 新工具 + 本周技术热点。
- 风格：自包含单文件（CSS/JS 内嵌，无外部 CDN、无字体外链、无追踪），浅色简洁卡片式，系统字体栈，移动端自适应。
- GitHub 仓库卡片在英文描述下方附一行机器翻译中文（Google 公共翻译接口，MyMemory 兜底；失败则省略该行）。

## 5. 自动化与部署

- GitHub Actions cron：每天 UTC 00:30（北京时间 08:30）运行。
- 部署方式：`actions/configure-pages` + `upload-pages-artifact` + `deploy-pages`，使用内置 `GITHUB_TOKEN`，无需个人 Token。
- 公开仓库：`yuhaven/tech-daily`，成品地址 `https://yuhaven.github.io/tech-daily/`。
- 每次运行保留当日 JSON 快照到 `data/`，历史更新记录由 Git 提交留档。

## 6. 容错与限流

- 每个数据源独立采集、独立容错：单个源失败不影响其他板块。
- GitHub 抓取失败自动降级到 Search API；Search API 未认证限流 10 次/分钟，控制请求数。
- RSS 逐源容错；页面生成失败时保留上一次成功页面。
- cron 运行耗时控制在几分钟内，避免触发 Actions 超时。

## 7. 验收标准

- 本地运行三个采集脚本 + 生成器，产出包含真实数据的 index.html。
- 页面三板块数据齐全、来源标注清楚、可读性强、移动端可用。
- GitHub Actions 定时触发后自动部署，公网可访问且数据为当日快照。

## 8. 非目标（YAGNI）

- 不做用户登录、评论、搜索。
- 不做历史趋势图表（初期版本）。
- 不翻译新闻标题。
