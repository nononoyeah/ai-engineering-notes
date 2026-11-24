from dataclasses import dataclass


@dataclass
class CleanedText:
    """文本清洗结果。"""

    original_text: str
    cleaned_text: str


def clean_text(text: str) -> CleanedText:
    """
    清洗文本中的基础格式噪声。

    当前处理：
    1. 去除文本首尾空白。
    2. 将连续空格和制表符合并为一个空格。
    3. 将连续空行压缩为一个空行。

    原始文本始终保留。
    """
    import re

    original_text = text

    # 统一换行符
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")

    # 合并连续空格和制表符，但不处理换行符
    cleaned = re.sub(r"[^\S\n]+", " ", cleaned)

    # 将连续空行压缩为一个空行
    cleaned = re.sub(r"\n[ \t]*\n+", "\n\n", cleaned)

    # 去除首尾空白
    cleaned = cleaned.strip()

    return CleanedText(
        original_text=original_text,
        cleaned_text=cleaned,
    )
