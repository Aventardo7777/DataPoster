# -*- coding: utf-8 -*-
"""SVG 海报渲染模块：把统计结果排版成一张杂志风信息图海报。

整体版式（1080 x 1440，3:4 竖版）:
    ┌────────────────────────┐
    │  标题色块 + 副标题 + 日期  │
    │  超大数字  │  TOP 1 卡片   │
    │  [样本数][均值][最大][最小] │
    │  TOP N 条形图（横向色带）  │
    │  页脚：出处与生成时间       │
    └────────────────────────┘
"""

from .analyze import fmt_number

POSTER_W, POSTER_H = 1080, 1440
MARGIN = 72
FONT_STACK = "'PingFang SC', 'Microsoft YaHei', 'Noto Sans SC', sans-serif"


# ---------------------------------------------------------------- 工具函数

def _esc(text):
    """XML 转义，防止数据里的 & < > 破坏 SVG 结构。"""
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _clip(text, max_chars):
    """超长文本截断加省略号，保证不溢出版面。"""
    text = str(text)
    return text if len(text) <= max_chars else text[: max_chars - 1] + "…"


def _text(x, y, content, size, color, weight="normal", anchor="start",
          opacity=1.0, spacing=None):
    """生成一行 <text>；统一字体栈，opacity 控制灰度层级。"""
    extra = ""
    if spacing:
        extra += " letter-spacing='%s'" % spacing
    if opacity < 1.0:
        extra += " opacity='%s'" % opacity
    return ("<text x='%d' y='%d' font-family=\"%s\" font-size='%d' "
            "font-weight='%s' fill='%s' text-anchor='%s'%s>%s</text>\n"
            % (x, y, FONT_STACK, size, weight, color, anchor, extra,
               _esc(content)))


def _fit_font_size(text, base, max_chars):
    """文本越长字号越小，避免大数字撑破画布。"""
    if len(str(text)) <= max_chars:
        return base
    return max(int(base * max_chars / len(str(text))), base // 2)


# ---------------------------------------------------------------- 分区渲染

def _render_header(theme, title, subtitle, generated):
    """顶部标题色块：杂志封面式的第一屏。"""
    t = theme
    parts = []
    parts.append("<rect x='0' y='0' width='%d' height='330' fill='%s'/>\n"
                 % (POSTER_W, t["primary"]))
    # 右上角装饰同心圆，打破大面积色块的呆板
    parts.append("<circle cx='985' cy='52' r='150' fill='%s' opacity='0.16'/>\n"
                 % t["secondary"])
    parts.append("<circle cx='1020' cy='30' r='88' fill='%s' opacity='0.28'/>\n"
                 % t["secondary"])
    # 顶部小标签
    parts.append(_text(MARGIN, 84, "DATA POSTER", 22,
                       t["bg"], "bold", spacing="6"))
    parts.append(_text(POSTER_W - MARGIN, 84, generated, 22,
                       t["bg"], "normal", anchor="end", opacity=0.85))
    # 主标题（过长自动缩小字号）
    title_size = _fit_font_size(title, 66, 13)
    parts.append(_text(MARGIN, 190, _clip(title, 18), title_size,
                       t["bg"], "bold"))
    # 标题下的强调短横线
    parts.append("<rect x='%d' y='222' width='132' height='12' "
                 "rx='6' fill='%s'/>\n" % (MARGIN, t["secondary"]))
    # 副标题
    if subtitle:
        parts.append(_text(MARGIN, 286, _clip(subtitle, 30), 28,
                           t["bg"], "normal", opacity=0.9))
    return "".join(parts)


def _render_hero(theme, hero_value, hero_label, unit, top1):
    """超大数字区 + TOP 1 卡片 —— 海报的记忆点。"""
    t = theme
    parts = []
    top_y = 396

    # 左侧：指标名（附单位）+ 超大数字（单位放标签行，避免压到右侧卡片）
    label_line = hero_label + ((" · " + unit) if unit else "")
    parts.append(_text(MARGIN, top_y + 8, label_line, 24, t["sub"],
                      "bold", spacing="3"))
    num_str = fmt_number(hero_value)
    # 超长数字自动缩号（max 6 字符宽度），确保不会压到右侧 TOP 1 卡片
    num_size = _fit_font_size(num_str, 150, 6)
    parts.append(_text(MARGIN, top_y + 168, num_str, num_size,
                       t["accent"], "bold"))

    # 右侧：TOP 1 卡片
    if top1:
        card_x, card_y, card_w, card_h = 596, top_y - 26, 412, 226
        parts.append("<rect x='%d' y='%d' width='%d' height='%d' rx='26' "
                     "fill='%s'/>\n" % (card_x, card_y, card_w, card_h,
                                        t["card"]))
        parts.append(_text(card_x + 34, card_y + 56, "TOP 1", 24,
                           t["primary"], "bold", spacing="4"))
        parts.append(_text(card_x + 34, card_y + 126,
                           _clip(top1[0], 9), 46, t["ink"], "bold"))
        val_str = fmt_number(top1[1])
        parts.append(_text(card_x + 34, card_y + 186, val_str
                           + ((" " + unit) if unit else ""),
                           _fit_font_size(val_str, 38, 9), t["primary"],
                           "bold"))
    return "".join(parts)


def _render_stat_cards(theme, summary, unit):
    """四宫格统计卡片：样本数 / 平均值 / 最大值 / 最小值。"""
    t = theme
    cards = [
        ("样本数", fmt_number(summary["count"], 0)),
        ("平均值", fmt_number(summary["mean"])),
        ("最大值", fmt_number(summary["vmax"])),
        ("最小值", fmt_number(summary["vmin"])),
    ]
    gap, y, h = 24, 680, 158
    w = (POSTER_W - MARGIN * 2 - gap * 3) // 4
    parts = []
    for i, (name, value) in enumerate(cards):
        x = MARGIN + i * (w + gap)
        parts.append("<rect x='%d' y='%d' width='%d' height='%d' rx='20' "
                     "fill='%s'/>\n" % (x, y, w, h, t["card"]))
        parts.append(_text(x + 26, y + 56, name, 22, t["sub"], "bold"))
        size = _fit_font_size(value, 40, 7)
        parts.append(_text(x + 26, y + 118, _clip(value, 10), size,
                           t["ink"], "bold"))
    return "".join(parts)


def _render_bars(theme, top, label_header, value_header, unit):
    """TOP N 横向条形图：杂志排行榜式的色带。"""
    t = theme
    parts = []
    y0, y1 = 900, 1332
    parts.append(_text(MARGIN, y0 + 42, "TOP %d · %s 排行" % (len(top),
                       label_header or "条目"), 32, t["ink"], "bold"))

    row_h = (y1 - (y0 + 78)) / max(len(top), 1)
    bar_h = min(30, int(row_h * 0.62))
    track_x, track_w = 330, 540
    vmax = top[0][1] if top else 1

    for i, (name, value) in enumerate(top):
        cy = y0 + 78 + i * row_h + row_h / 2
        # 排名序号
        parts.append(_text(MARGIN + 6, cy + 8, "%02d" % (i + 1), 24,
                           t["sub"], "bold"))
        # 条目标签名（右对齐，留出条形图起点；7 字截断避免撞上序号）
        parts.append(_text(track_x - 18, cy + 8, _clip(name, 7), 23,
                           t["ink"], "bold", anchor="end"))
        # 底轨
        parts.append("<rect x='%d' y='%.1f' width='%d' height='%d' rx='%d' "
                     "fill='%s'/>\n" % (track_x, cy - bar_h / 2, track_w,
                                        bar_h, bar_h // 2, t["card"]))
        # 数值条（第 1 名用强调色，其余主副色交替）
        w = max(int(track_w * value / vmax), bar_h)
        color = t["accent"] if i == 0 else (
            t["primary"] if i % 2 == 1 else t["secondary"])
        parts.append("<rect x='%d' y='%.1f' width='%d' height='%d' rx='%d' "
                     "fill='%s'/>\n" % (track_x, cy - bar_h / 2, w, bar_h,
                                        bar_h // 2, color))
        # 条形末端的数值
        val_str = fmt_number(value)
        parts.append(_text(track_x + track_w + 22, cy + 8, val_str,
                           _fit_font_size(val_str, 24, 8), t["ink"], "bold"))
    if unit:
        parts.append(_text(POSTER_W - MARGIN, y0 + 42, "单位: %s" % unit, 22,
                           t["sub"], "normal", anchor="end"))
    return "".join(parts)


def _render_footer(theme, generated):
    """页脚：出处标识 + 生成时间。"""
    t = theme
    y = 1398
    parts = ["<line x1='%d' y1='%d' x2='%d' y2='%d' stroke='%s' "
             "stroke-width='2' opacity='0.35'/>\n"
             % (MARGIN, y - 34, POSTER_W - MARGIN, y - 34, t["sub"])]
    parts.append(_text(MARGIN, y, "DATA POSTER · 数据可视化为一见倾心而生",
                       22, t["sub"], "bold", spacing="2"))
    parts.append(_text(POSTER_W - MARGIN, y, "Generated %s · DataPoster v1.0"
                       % generated, 22, t["sub"], "normal", anchor="end"))
    return "".join(parts)


# ---------------------------------------------------------------- 主入口

def render_poster(title, subtitle, hero, top, summary, label_header,
                  value_header, theme):
    """组装整张海报。

    参数:
        title / subtitle  标题与副标题（来自 CLI 或列名）
        hero              (数值, 指标名) 超大数字区内容
        top               [(标签, 数值), ...] 排行榜
        summary           analyze.summarize() 的统计结果
        label_header / value_header  两列的表头名
        theme             主题色板 dict
    """
    top1 = top[0] if top else None
    svg = []
    svg.append("<?xml version='1.0' encoding='UTF-8'?>\n")
    svg.append("<svg xmlns='http://www.w3.org/2000/svg' "
               "viewBox='0 0 %d %d' width='%d' height='%d' "
               "font-family=\"%s\">\n"
               % (POSTER_W, POSTER_H, POSTER_W, POSTER_H, FONT_STACK))
    svg.append("<rect width='%d' height='%d' fill='%s'/>\n"
               % (POSTER_W, POSTER_H, theme["bg"]))
    svg.append(_render_header(theme, title, subtitle, summary["generated"]))
    svg.append(_render_hero(theme, hero[0], hero[1], summary["unit"], top1))
    svg.append(_render_stat_cards(theme, summary, summary["unit"]))
    if top:
        svg.append(_render_bars(theme, top, label_header, value_header,
                               summary["unit"]))
    svg.append(_render_footer(theme, summary["generated"]))
    svg.append("</svg>\n")
    return "".join(svg)
