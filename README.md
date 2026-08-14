# Daily Tech Pulse · 每日技术情报

每天自动更新的静态情报页，聚合三类真实、有热度的信息：

1. **GitHub Star 排行榜**：每日 / 每周 / 每月新增 star 最多的仓库（来源：GitHub Trending）。
2. **AI 前沿新闻**：按真实热度（Hacker News 投票分）排序的 AI 新闻，辅以 TechCrunch、VentureBeat、The Verge、MIT Technology Review、Ars Technica 等欧美主流科技媒体的最新报道。
3. **最新技术 & 工具**：Hacker News "Show HN" 高分新工具与本周技术热点。

## 访问地址

<https://yuhaven.github.io/tech-daily/>

## 更新机制

GitHub Actions 每天 UTC 00:30（北京时间 08:30）自动运行：

1. 运行三个采集脚本抓取真实数据；
2. 生成自包含的静态页面 `index.html`；
3. 将当日 JSON 快照提交回仓库留档；
4. 自动部署到 GitHub Pages。

## 本地运行

```bash
python scripts/collect_github.py
python scripts/collect_news.py
python scripts/collect_tools.py
python scripts/generate_site.py
```

然后打开生成的 `index.html`，或运行 `python -m http.server 8123` 后访问 <http://127.0.0.1:8123>。

纯 Python 标准库实现，无第三方依赖。

GitHub 仓库描述、AI 新闻标题、工具标题会自动附带一行机器翻译的中文参考（带“译：”前缀），原文保持权威。

## 数据来源与免责声明

所有内容均来自公开 API / RSS：GitHub Trending、Hacker News（Firebase & Algolia API）、上述科技媒体官方 RSS。页面仅做聚合展示，点击条目可跳转原文；内容版权归原作者所有。
