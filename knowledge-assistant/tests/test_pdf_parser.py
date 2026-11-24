import pymupdf
import pytest

from backend.app.document_parser.pdf_parser import (
    PDFDocumentError,
    open_pdf_document,
)
from backend.app.document_parser.pdf_parser import extract_pdf_content


def create_test_pdf(path):
    """动态生成一份最小 PDF 测试文件。"""
    document = pymupdf.open()
    document.new_page()
    document.save(path)
    document.close()


def test_open_valid_pdf(tmp_path):
    pdf_path = tmp_path / "valid.pdf"
    create_test_pdf(pdf_path)

    document = open_pdf_document(pdf_path)

    try:
        assert document.is_pdf
        assert document.page_count == 1
    finally:
        document.close()


def test_open_nonexistent_pdf():
    with pytest.raises(FileNotFoundError, match="PDF 文件不存在"):
        open_pdf_document("not_exists.pdf")


def test_open_invalid_pdf(tmp_path):
    invalid_path = tmp_path / "invalid.pdf"
    invalid_path.write_text("这不是一个有效的 PDF 文件", encoding="utf-8")

    with pytest.raises(PDFDocumentError, match="无法读取 PDF 文件"):
        open_pdf_document(invalid_path)


def create_multi_page_pdf(path):
    """创建包含不同页面文本的多页 PDF。"""
    document = pymupdf.open()

    page1 = document.new_page()
    page1.insert_text((72, 72), "First page")

    page2 = document.new_page()
    page2.insert_text((72, 72), "Second page")

    page3 = document.new_page()
    page3.insert_text((72, 72), "Third page")

    document.save(path)
    document.close()


def test_extract_pdf_content_preserves_page_order(tmp_path):
    pdf_path = tmp_path / "multi_page.pdf"
    create_multi_page_pdf(pdf_path)

    result = extract_pdf_content(pdf_path)

    assert result.filename == "multi_page.pdf"
    assert result.total_pages == 3
    assert len(result.pages) == 3

    assert result.pages[0].page_number == 1
    assert "First page" in result.pages[0].text

    assert result.pages[1].page_number == 2
    assert "Second page" in result.pages[1].text

    assert result.pages[2].page_number == 3
    assert "Third page" in result.pages[2].text
