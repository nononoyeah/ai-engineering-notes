import pymupdf
import pytest

from backend.app.document_parser.pdf_parser import (
    PDFDocumentError,
    open_pdf_document,
)


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