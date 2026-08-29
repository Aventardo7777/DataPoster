# -*- coding: utf-8 -*-
"""DataPoster —— 把 CSV 数据一键变成杂志风信息图海报。

纯 Python 标准库实现，零第三方依赖。

对外主要接口:
    from dataposter import make_poster
    make_poster("data.csv", title="我的标题", theme="ocean")
"""

from .analyze import (load_csv, detect_columns, summarize, fmt_number,
                      pick_hero_number)
from .render import render_poster
from .themes import THEMES, get_theme

__version__ = "1.0.0"
__all__ = ["make_poster", "load_csv", "detect_columns", "summarize",
           "render_poster", "fmt_number", "THEMES", "get_theme",
           "__version__"]


def make_poster(csv_path, title=None, subtitle=None, theme="sunset",
                top=8, label=None, value=None, metric="total",
                output=None):
    """一行代码：CSV -> 杂志风 SVG 海报。

    参数:
        csv_path  输入 CSV 路径
        title / subtitle  海报标题（缺省时自动生成）
        theme     配色主题，见 themes.THEMES
        top       排行榜条数（1~10）
        label / value  指定标签列 / 数值列（缺省时自动识别）
        metric    超大数字使用的统计量 total/mean/max/min/std/count
        output    输出路径（缺省: output/<csv名>_<主题>.svg）

    返回:
        输出文件的绝对路径
    """
    import os

    fields, rows = load_csv(csv_path)
    label_col = label or detect_columns(fields, rows)[0]
    value_col = value or detect_columns(fields, rows)[1]
    summary = summarize(rows, value_col, top_n=max(1, min(top, 10)),
                        label_col=label_col)
    hero = pick_hero_number(summary, metric)

    svg = render_poster(
        title or ("%s 排行" % value_col),
        subtitle or ("基于 %d 条记录的自动统计 · 数据文件: %s"
                     % (summary["count"], os.path.basename(csv_path))),
        hero, summary["top"], summary, label_col, value_col,
        get_theme(theme),
    )

    out = output or "output/%s_%s.svg" % (
        os.path.splitext(os.path.basename(csv_path))[0], theme)
    out_dir = os.path.dirname(out)
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(svg)
    return os.path.abspath(out)
