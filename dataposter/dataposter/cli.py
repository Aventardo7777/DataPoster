# -*- coding: utf-8 -*-
"""DataPoster 命令行入口。

用法示例:
    python -m dataposter examples/cities_gdp.csv --theme sunset
    python -m dataposter data.csv -t "我的标题" -s "副标题" --top 10 -o out.svg
    python -m dataposter data.csv --list-themes
"""

import argparse
import os
import sys

from . import __version__
from .analyze import (load_csv, detect_columns, summarize, pick_hero_number,
                      fmt_number)
from .render import render_poster
from .themes import THEMES, get_theme


def build_parser():
    p = argparse.ArgumentParser(
        prog="dataposter",
        description="DataPoster —— 把 CSV 数据一键变成杂志风信息图海报（纯 Python 标准库，零依赖）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例:\n"
               "  python -m dataposter examples/cities_gdp.csv\n"
               "  python -m dataposter data.csv --theme ocean --top 10 -o poster.svg\n"
               "  python -m dataposter data.csv --value GDP --metric max --list-themes",
    )
    p.add_argument("csv", nargs="?", help="输入的 CSV 文件路径")
    p.add_argument("-o", "--output", default=None,
                   help="输出 SVG 路径（默认: <输入名>_<主题>.svg，保存到 output/ 目录）")
    p.add_argument("-t", "--title", default=None, help="海报主标题（默认取数值列名）")
    p.add_argument("-s", "--subtitle", default=None,
                   help="副标题（默认: '基于 N 条记录的自动统计 · 数据来源: 文件名'）")
    p.add_argument("--theme", default="sunset",
                   help="配色主题: %s（默认 sunset）" % "/".join(THEMES))
    p.add_argument("--top", type=int, default=8,
                   help="排行榜展示条数，1~10（默认 8）")
    p.add_argument("--label", default=None, help="手动指定标签列（默认自动识别）")
    p.add_argument("--value", default=None, help="手动指定数值列（默认自动识别）")
    p.add_argument("--metric", default="total",
                   choices=["total", "mean", "max", "min", "std", "count"],
                   help="左上角超大数字使用哪个统计量（默认 total）")
    p.add_argument("--list-themes", action="store_true",
                   help="仅列出全部可用主题后退出")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)

    if args.list_themes:
        print("可用主题:")
        for name in THEMES:
            print("  - %-8s" % name)
        return 0

    if not args.csv:
        build_parser().print_help()
        return 1

    if not os.path.isfile(args.csv):
        print("[错误] 找不到文件: %s" % args.csv)
        return 1

    # 1. 读取并识别列
    fields, rows = load_csv(args.csv)
    auto_label, auto_value, numeric_cols = detect_columns(fields, rows)
    label_col = args.label or auto_label
    value_col = args.value or auto_value
    if value_col is None:
        print("[错误] 没有检测到数值列，请用 --value 手动指定，"
              "或检查 CSV 是否包含数字。")
        return 1
    if value_col not in fields or label_col not in fields:
        print("[错误] 指定的列名不存在。CSV 中的列: %s" % ", ".join(fields))
        return 1

    print("[识别] 标签列 -> %s | 数值列 -> %s（可用 --label/--value 覆盖）"
          % (label_col, value_col))
    if len(numeric_cols) > 1:
        print("[提示] 检测到多个数值列: %s，默认使用区分度最高的一列"
              % ", ".join(numeric_cols))

    # 2. 统计
    summary = summarize(rows, value_col, top_n=max(1, min(args.top, 10)),
                        label_col=label_col)

    # 3. 渲染
    theme = get_theme(args.theme)
    hero = pick_hero_number(summary, args.metric)
    title = args.title or ("%s 排行" % value_col)
    subtitle = args.subtitle or ("基于 %d 条记录的自动统计 · 数据文件: %s"
                                 % (summary["count"],
                                    os.path.basename(args.csv)))
    svg = render_poster(title, subtitle, hero, summary["top"], summary,
                        label_col, value_col, theme)

    # 4. 落盘
    out = args.output or "output/%s_%s.svg" % (
        os.path.splitext(os.path.basename(args.csv))[0], args.theme)
    out_dir = os.path.dirname(out)
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(svg)

    # 5. 终端小结（同样保持杂志感）
    print()
    print("=" * 46)
    print("  海报已生成 -> %s" % out)
    print("=" * 46)
    print("  主题: %s | 超大数字: %s %s"
          % (args.theme, fmt_number(hero[0]), summary["unit"]))
    print("  合计 %s | 均值 %s | 样本 %d"
          % (fmt_number(summary["total"]), fmt_number(summary["mean"]),
             summary["count"]))
    if summary["top"]:
        print("  TOP 1: %s (%s%s)"
              % (summary["top"][0][0], fmt_number(summary["top"][0][1]),
                 summary["unit"]))
    print()
    print("  用浏览器打开 SVG 即可查看 / 截图分享。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
