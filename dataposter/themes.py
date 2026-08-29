# -*- coding: utf-8 -*-
"""主题色板：为海报提供杂志风格的配色方案。

每个主题包含:
    bg        海报底色
    ink       正文文字色
    sub       次级文字色
    primary   主色（标题色块 / 重点条形）
    secondary 副色（次级条形 / 卡片底）
    accent    强调色（大数字 / 高亮点）
    card      统计卡片底色
"""

# 主题注册表：新增主题只需在这里加一项
THEMES = {
    "sunset": {  # 落日橘 —— 编辑部经典暖色
        "bg": "#FFF6EC",
        "ink": "#2B2118",
        "sub": "#8A7A6A",
        "primary": "#E85D2F",
        "secondary": "#F4A259",
        "accent": "#E85D2F",
        "card": "#FFE8D6",
    },
    "ocean": {  # 深海蓝 —— 冷静克制的数据感
        "bg": "#F0F6FB",
        "ink": "#14283C",
        "sub": "#6E8398",
        "primary": "#1B6CA8",
        "secondary": "#7FB3D5",
        "accent": "#12507E",
        "card": "#DCEBF7",
    },
    "forest": {  # 森林绿 —— 自然沉稳
        "bg": "#F4FAF4",
        "ink": "#1E2E22",
        "sub": "#6F8577",
        "primary": "#2E7D4F",
        "secondary": "#8CC5A1",
        "accent": "#1E5C39",
        "card": "#E1F2E6",
    },
    "ink": {  # 水墨黑 —— 极简高级感
        "bg": "#F7F7F5",
        "ink": "#1A1A1A",
        "sub": "#8C8C8C",
        "primary": "#1A1A1A",
        "secondary": "#B9B9B9",
        "accent": "#C0392B",
        "card": "#ECECE8",
    },
    "candy": {  # 糖果粉 —— 活泼醒目
        "bg": "#FFF3F8",
        "ink": "#3A1F2E",
        "sub": "#A1768C",
        "primary": "#E0447C",
        "secondary": "#F79AC0",
        "accent": "#C2185B",
        "card": "#FFE1EE",
    },
    "cyber": {  # 赛博紫 —— 电子潮流
        "bg": "#F5F2FC",
        "ink": "#241B3A",
        "sub": "#7A6E9B",
        "primary": "#6C3FC5",
        "secondary": "#A98BEA",
        "accent": "#4B1E9E",
        "card": "#EAE2FA",
    },
}

DEFAULT_THEME = "sunset"


def get_theme(name):
    """按名称取主题；不存在时回退到默认主题并给出提示。"""
    if name in THEMES:
        return THEMES[name]
    print("[提示] 未找到主题 '%s'，已回退到 '%s'。可用主题: %s"
          % (name, DEFAULT_THEME, ", ".join(THEMES)))
    return THEMES[DEFAULT_THEME]
