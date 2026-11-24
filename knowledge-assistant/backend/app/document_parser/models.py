from dataclasses import dataclass, field


@dataclass
class PageContent:
    """单个 PDF 页面的解析结果。"""

    page_number: int
    text: str
    cleaned_text: str = ""


@dataclass
class DocumentContent:
    """整个 PDF 文档的解析结果。"""

    filename: str
    total_pages: int
    pages: list[PageContent] = field(default_factory=list)