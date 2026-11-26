from pathlib import Path

from markdown_it import MarkdownIt

from backend.app.document_parser.models import (
    DocumentContent,
    PageContent,
)
from backend.app.document_parser.text_cleaner import clean_markdown_text

_MARKDOWN_PARSER = MarkdownIt("commonmark")
_CODE_BLOCK_TOKENS = ("fence", "code_block", "html_block")


class MarkdownDocumentError(Exception):
    """Markdown 文档读取或校验失败。"""


def _read_markdown_text(path: Path) -> str:
    """读取 Markdown 文件内容，兼容带 BOM 的 UTF-8。"""
    if not path.exists():
        raise FileNotFoundError(f"Markdown 文件不存在：{path}")

    if not path.is_file():
        raise MarkdownDocumentError(f"指定路径不是文件：{path}")

    try:
        return path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as exc:
        raise MarkdownDocumentError(f"无法读取 Markdown 文件：{path}，原因：{exc}") from exc


def _heading_title(tokens: list, index: int) -> str:
    """取标题行的纯文本，去掉加粗、斜体等内联标记。"""
    inline_token = tokens[index + 1]
    parts = [
        "\n" if child.type in ("softbreak", "hardbreak") else child.content
        for child in (inline_token.children or [])
    ]
    return " ".join("".join(parts).split())


def _front_matter_end(lines: list[str]) -> int:
    """返回文件开头 YAML front matter 的结束行号，不存在时返回 0。"""
    if not lines or lines[0].strip() != "---":
        return 0

    for index in range(1, len(lines)):
        if lines[index].strip() in ("---", "..."):
            return index + 1

    return 0


def _collect_headings_and_code_lines(
    tokens: list,
    front_matter_end: int,
) -> tuple[list[tuple[int, int, str]], set[int]]:
    """从解析结果中取标题切分点和代码块行号。"""
    headings: list[tuple[int, int, str]] = []
    code_lines: set[int] = set()

    for index, token in enumerate(tokens):
        if token.type in _CODE_BLOCK_TOKENS and token.map:
            code_lines.update(range(*token.map))
        elif (
            token.type == "heading_open"
            and token.level == 0
            and token.map
            and token.map[0] >= front_matter_end
            and index + 1 < len(tokens)
        ):
            headings.append(
                (token.map[0], int(token.tag[1]), _heading_title(tokens, index))
            )

    return headings, code_lines


def extract_markdown_content(md_path: str | Path) -> DocumentContent:
    """
    读取 Markdown 文档并按顶层标题切分为节。

    每个节从其标题行开始，到下一个任意层级标题之前结束；
    第一个标题之前的内容（含 front matter）作为层级 0 的前言节。
    节的 text 保留原文（仅统一换行符），cleaned_text 单独保存清洗结果。
    """
    path = Path(md_path)
    text = _read_markdown_text(path)

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    lined = [line + "\n" for line in lines[:-1]] + [lines[-1]]

    front_matter_end = _front_matter_end(lines)
    tokens = _MARKDOWN_PARSER.parse(text)
    headings, code_lines = _collect_headings_and_code_lines(tokens, front_matter_end)

    bounds = ([(0, 0, "")] if not headings or headings[0][0] > 0 else []) + headings

    pages: list[PageContent] = []
    heading_stack: list[tuple[int, str]] = []

    for position, (start, level, title) in enumerate(bounds):
        end = bounds[position + 1][0] if position + 1 < len(bounds) else len(lines)

        while heading_stack and heading_stack[-1][0] >= level:
            heading_stack.pop()

        if level:
            heading_stack.append((level, title))

        raw_text = "".join(lined[start:end])

        if not raw_text.strip():
            continue

        pages.append(
            PageContent(
                page_number=len(pages) + 1,
                text=raw_text,
                cleaned_text=clean_markdown_text(lines, start, end, code_lines),
                heading_path=" > ".join(title for _, title in heading_stack),
                heading_level=level,
            )
        )

    if not pages:
        raise MarkdownDocumentError(f"Markdown 文档没有可提取的文本内容：{path}")

    return DocumentContent(
        filename=path.name,
        total_pages=len(pages),
        pages=pages,
        source_type="markdown",
    )
