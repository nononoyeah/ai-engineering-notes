from dataclasses import dataclass, field


@dataclass
class PageContent:
    """单个文档片段的解析结果：PDF 为页，Markdown 为节。"""

    page_number: int
    text: str
    cleaned_text: str = ""
    heading_path: str = ""
    heading_level: int = 0


@dataclass
class DocumentContent:
    """整个文档的解析结果。"""

    filename: str
    total_pages: int
    pages: list[PageContent] = field(default_factory=list)
    source_type: str = "pdf"