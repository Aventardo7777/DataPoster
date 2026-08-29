# -*- coding: utf-8 -*-
"""数据分析模块：读取 CSV、自动识别标签列与数值列、计算统计量。

设计目标：用户只丢进来一个 CSV，不需要写任何配置，
工具就能猜出「哪一列是名字、哪一列是数值」，并算好海报需要的所有数字。
"""

import csv
import statistics
from datetime import date


def _try_float(text):
    """尝试把文本转成 float；处理千分位逗号与百分号。失败返回 None。"""
    if text is None:
        return None
    s = str(text).strip().replace(",", "").replace("%", "")
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _column_values(rows, col):
    """取某列的全部非空原始值。"""
    return [r.get(col, "").strip() for r in rows if r.get(col) is not None
            and str(r.get(col)).strip() != ""]


def _numeric_ratio(rows, col):
    """某列中可解析为数字的占比（0~1）。"""
    values = _column_values(rows, col)
    if not values:
        return 0.0
    ok = sum(1 for v in values if _try_float(v) is not None)
    return ok / len(values)


def load_csv(path, encoding="utf-8-sig"):
    """读取 CSV 为 (fieldnames, rows)。utf-8-sig 兼容 Excel 导出的 BOM 头。"""
    for enc in (encoding, "gbk"):  # 先 UTF-8 再 GBK，覆盖中文 Windows 场景
        try:
            with open(path, newline="", encoding=enc) as f:
                reader = csv.DictReader(f)
                # 去掉表头前后的空白，避免 "城市, GDP" 解析出 " GDP"
                reader.fieldnames = [fn.strip() for fn in reader.fieldnames]
                rows = [dict(r) for r in reader if any(
                    (v or "").strip() for v in r.values())]
            if reader.fieldnames:
                return list(reader.fieldnames), rows
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise ValueError("无法解析文件 %s（尝试过 utf-8 / gbk 编码）" % path)


def detect_columns(fields, rows):
    """自动识别标签列与数值列。

    规则（简单但够用）:
      - 标签列: 第一列「大部分不是数字」的列（通常是名字/地名/机构名）
      - 数值列: 所有「大部分是数字」的列；
        默认取数值种类最多的一列（区分度最高，画条形图最有信息量）
    """
    numeric_cols, text_cols = [], []
    for col in fields:
        ratio = _numeric_ratio(rows, col)
        (numeric_cols if ratio >= 0.7 else text_cols).append(col)

    label = text_cols[0] if text_cols else fields[0]

    value = None
    if numeric_cols:
        # 取「方差最大」的数值列作为主列：
        # 区分度高的列画条形图最有信息量，也能避开"排名"这类低方差列
        def _spread(col):
            vals = [v for v in (_try_float(x) for x in
                                _column_values(rows, col)) if v is not None]
            if len(vals) < 2:
                return 0.0
            mean = sum(vals) / len(vals)
            return sum((v - mean) ** 2 for v in vals) / len(vals)

        value = max(numeric_cols, key=_spread)
    return label, value, numeric_cols


def top_rows(rows, label_col, value_col, n=8):
    """按数值列降序取前 n 行，返回 [(标签, 数值), ...]。"""
    pairs = []
    for r in rows:
        val = _try_float(r.get(value_col, ""))
        lab = str(r.get(label_col, "")).strip()
        if val is not None and lab:
            pairs.append((lab, val))
    pairs.sort(key=lambda p: p[1], reverse=True)
    return pairs[:n]


def summarize(rows, value_col, top_n=8, label_col=None):
    """计算海报所需的全部统计量。

    返回 dict:
        count / total / mean / vmax / vmin / std
        top       [(标签, 数值), ...] 前 top_n
        unit      数值列的推断单位（从列名括号里抓，如 "GDP(亿元)" -> "亿元"）
        generated 生成日期字符串
    """
    values = [v for v in (_try_float(r.get(value_col, "")) for r in rows)
              if v is not None]
    if not values:
        raise ValueError("数值列 '%s' 中没有可解析的数字" % value_col)

    unit = ""
    for ch in ("（", "("):
        if ch in value_col:
            close = "）" if ch == "（" else ")"
            unit = value_col.split(ch, 1)[1].split(close, 1)[0]
            break

    label = label_col or ""
    top = top_rows(rows, label, value_col, top_n) if label else []

    return {
        "count": len(values),
        "total": sum(values),
        "mean": statistics.fmean(values),
        "vmax": max(values),
        "vmin": min(values),
        "std": statistics.pstdev(values) if len(values) > 1 else 0.0,
        "top": top,
        "unit": unit,
        "generated": date.today().strftime("%Y.%m.%d"),
    }


def pick_hero_number(summary, metric):
    """根据 --metric 选择海报左上角的「超大数字」。

    metric: total / mean / max / min / std / count
    """
    mapping = {
        "total": (summary["total"], "合计"),
        "mean": (summary["mean"], "平均值"),
        "max": (summary["vmax"], "最大值"),
        "min": (summary["vmin"], "最小值"),
        "std": (summary["std"], "标准差"),
        "count": (float(summary["count"]), "样本数"),
    }
    return mapping.get(metric, mapping["total"])


def fmt_number(x, digits=1):
    """数字美化：整数不带小数，小数保留 digits 位，加千分位。"""
    if abs(x - round(x)) < 1e-9:
        return "{:,}".format(int(round(x)))
    return "{:,.{d}f}".format(x, d=digits)
