# 上海交通大学物理方向 · 师资检索 / SJTU Physics Faculty Directory

一个自包含的网页，收录**上海交通大学物理与天文学院 198 位教师/科研人员**，支持按学科、院系/研究所、关键词搜索与筛选。数据抓取于 2026-10-01，每条记录均链接到其在物理与天文学院官网的官方个人主页。

**在线访问 / Live:** https://SZhang0314.github.io/sjtu-physics-directory/

## 覆盖范围 / Scope

| 单位 / 研究所 | 人数 |
|---|---|
| 凝聚态物理研究所 / 研究部 | 51 |
| 激光等离子体研究所 | 39 |
| 粒子与核物理研究所 / 研究部 | 31 |
| 光科学与技术研究所 | 25 |
| 天文系 / 天文与天体物理研究部 | 21 |
| 教学研究中心 | 15 |
| 交叉科学研究所 | 8 |
| 维尔切克量子中心 / 超快科学中心 | 5 |
| 物理与天文学院（院直属） | 3 |
| **合计** | **198** |

其中 **41 人** 为深度信息（`confidence: fine`：职称、研究方向、荣誉、简介、可得的邮箱/主页/代表性论文），
其余为名录级（`confidence: coarse`：姓名、职称、院系、官方个人主页链接；仍尽可能补齐研究方向、邮箱、荣誉等）。

> 说明：另有李政道研究所（TDLI）独立师资页面为动态加载（SPA），本目录以物理与天文学院官网「教师名录」与「教师名录(双聘)」为准，已覆盖其双聘师资。

## 数据来源 / Sources

- 教师名录：https://www.physics.sjtu.edu.cn/jsml.html
- 教师名录（双聘）：https://www.physics.sjtu.edu.cn/jsml_sp.html

每位教师记录中的 `sources` 字段列出实际使用的 URL，便于审计。

## 文件结构

```
sjtu-physics-directory/
├── data/
│   ├── faculty.json        # 数据源（source of truth）
│   ├── roster.json         # 官网名录原始抓取结果
│   ├── parsed.json         # 单人页面结构化解析结果
│   └── html/               # 官方个人页面快照
├── scripts/
│   ├── extract_roster.py   # 抓取并解析官网教师名录
│   ├── crawl.py            # 下载每位教师个人主页
│   ├── parse.py            # 解析个人主页头部字段（职称/方向/邮箱等）
│   ├── parse_pubs.py       # 解析代表性论文
│   └── assemble.py         # 汇总生成 faculty.json
├── index.html              # 单文件可搜索网页（内嵌数据+样式+脚本）
├── README.md
└── .nojekyll
```

## 重新生成 / Regenerate

```bash
python scripts/extract_roster.py    # 抓取官网名录
python scripts/crawl.py             # 下载个人主页
python scripts/parse.py             # 解析头部字段
python scripts/assemble.py          # 生成 faculty.json
python <search_prof>/scripts/build_site.py \
    --data data/faculty.json --out . \
    --title "上海交通大学物理方向 · 师资检索 / SJTU Physics Faculty Directory"
```

## 说明 / Notes

- 页面为单文件，双击 `index.html` 即可离线打开，也可直接部署到 GitHub Pages。
- 数据来自公开的官方师资页面；未在页面上出现的信息（邮箱、主页、代表作）一律留空，未做任何臆测。
- `generated_at`：2026-10-01。
