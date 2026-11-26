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


def clean_markdown_text(
    lines: list[str],
    start: int,
    end: int,
    code_lines: set[int],
) -> str:
    """
    清洗 Markdown 文本的空白噪声，保留 Markdown 语法。

    只处理 lines[start:end] 范围内的行，行号以整篇文档为基准。
    code_lines 中的行属于代码块，原样保留；其余行去除行尾空白，
    连续空行压缩为一个空行，并去除首尾空白行。
    """
    cleaned_lines: list[str] = []
    pending_blank = False

    for line_number in range(start, end):
        line = lines[line_number]
        in_code = line_number in code_lines

        if not in_code and not line.strip():
            pending_blank = True
            continue

        if pending_blank:
            cleaned_lines.append("")
            pending_blank = False

        cleaned_lines.append(line if in_code else line.rstrip())

    return "\n".join(cleaned_lines).strip("\n")
