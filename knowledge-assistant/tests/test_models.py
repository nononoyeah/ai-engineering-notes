from backend.app.document_parser.models import (
    DocumentContent,
    PageContent,
)


def test_document_content_with_single_page():
    page = PageContent(
        page_number=1,
        text="第一页内容",
    )

    document = DocumentContent(
        filename="example.pdf",
        total_pages=1,
        pages=[page],
    )

    assert document.filename == "example.pdf"
    assert document.total_pages == 1
    assert len(document.pages) == 1
    assert document.pages[0].page_number == 1
    assert document.pages[0].text == "第一页内容"


def test_document_content_with_multiple_pages():
    document = DocumentContent(
        filename="example.pdf",
        total_pages=3,
        pages=[
            PageContent(1, "第一页"),
            PageContent(2, ""),
            PageContent(3, "第三页"),
        ],
    )

    assert document.total_pages == 3
    assert len(document.pages) == 3
    assert document.pages[1].text == ""
    assert document.pages[2].page_number == 3


def test_document_content_default_pages_are_independent():
    first = DocumentContent(filename="a.pdf", total_pages=0)
    second = DocumentContent(filename="b.pdf", total_pages=0)

    first.pages.append(PageContent(1, "内容"))

    assert len(first.pages) == 1
    assert len(second.pages) == 0


def test_page_content_heading_fields_default_empty():
    page = PageContent(page_number=1, text="第一页内容")

    assert page.heading_path == ""
    assert page.heading_level == 0


def test_document_content_defaults_to_pdf_source():
    document = DocumentContent(filename="example.pdf", total_pages=1)

    assert document.source_type == "pdf"


def test_document_content_with_markdown_sections():
    page = PageContent(
        page_number=2,
        text="## 二级标题\n\n正文",
        cleaned_text="## 二级标题\n\n正文",
        heading_path="一级标题 > 二级标题",
        heading_level=2,
    )

    document = DocumentContent(
        filename="notes.md",
        total_pages=2,
        pages=[page],
        source_type="markdown",
    )

    assert document.source_type == "markdown"
    assert document.pages[0].heading_path == "一级标题 > 二级标题"
    assert document.pages[0].heading_level == 2