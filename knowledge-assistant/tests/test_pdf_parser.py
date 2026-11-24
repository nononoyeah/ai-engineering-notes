import pymupdf
import pytest

from backend.app.document_parser.pdf_parser import (
    PDFDocumentError,
    open_pdf_document,
)
from backend.app.document_parser.pdf_parser import extract_pdf_content
from unittest.mock import patch


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


def test_extract_pdf_content_preserves_blank_page(tmp_path):
    pdf_path = tmp_path / "blank_page.pdf"

    document = pymupdf.open()

    page1 = document.new_page()
    page1.insert_text((72, 72), "First page")

    document.new_page()  # 第二页保持空白

    page3 = document.new_page()
    page3.insert_text((72, 72), "Third page")

    document.save(pdf_path)
    document.close()

    result = extract_pdf_content(pdf_path)

    assert result.total_pages == 3
    assert len(result.pages) == 3
    assert result.pages[0].text.strip() == "First page"
    assert result.pages[1].page_number == 2
    assert result.pages[1].text.strip() == ""
    assert result.pages[2].text.strip() == "Third page"


def test_extract_pdf_content_rejects_image_only_pdf(tmp_path):
    pdf_path = tmp_path / "image_only.pdf"

    document = pymupdf.open()
    document.new_page()
    document.save(pdf_path)
    document.close()

    with pytest.raises(
        PDFDocumentError,
        match="没有可提取的文本内容",
    ):
        extract_pdf_content(pdf_path)


def test_extract_pdf_content_reports_page_extraction_error(tmp_path):
    pdf_path = tmp_path / "error_page.pdf"
    create_multi_page_pdf(pdf_path)

    original_load_page = pymupdf.Document.load_page

    def mock_load_page(document, page_index, *args, **kwargs):
        if page_index == 1:
            raise RuntimeError("模拟第二页读取失败")

        return original_load_page(
            document,
            page_index,
            *args,
            **kwargs,
        )

    with patch(
        "pymupdf.Document.load_page",
        new=mock_load_page,
    ):
        with pytest.raises(
            PDFDocumentError,
            match="第 2 页提取失败",
        ):
            extract_pdf_content(pdf_path)


def test_extract_pdf_content_preserves_original_and_cleaned_text(tmp_path):
    pdf_path = tmp_path / "cleaning_test.pdf"

    document = pymupdf.open()

    page1 = document.new_page()
    page1.insert_text(
        (72, 72),
        "First    page",
    )

    # 第二页保留为空白页
    document.new_page()

    page3 = document.new_page()
    page3.insert_text(
        (72, 72),
        "Third    page",
    )

    document.save(pdf_path)
    document.close()

    result = extract_pdf_content(pdf_path)

    assert result.total_pages == 3
    assert len(result.pages) == 3

    # 第一页：原始文本与清洗文本分别保存
    assert result.pages[0].page_number == 1
    assert "First" in result.pages[0].text
    assert "First page" in result.pages[0].cleaned_text

    # 第二页：空白页仍然保留
    assert result.pages[1].page_number == 2
    assert result.pages[1].cleaned_text == ""

    # 第三页：清洗结果仍对应第三页
    assert result.pages[2].page_number == 3
    assert "Third" in result.pages[2].text
    assert "Third page" in result.pages[2].cleaned_text
    
