import json

import pymupdf
import pytest

from backend.app.document_parser.pipeline import process_pdf
from backend.app.document_parser.pdf_parser import PDFDocumentError


def create_pdf(path, pages):
    """按 pages 中的字符串列表创建 PDF；空字符串代表空白页。"""
    document = pymupdf.open()
    for text in pages:
        page = document.new_page()
        if text:
            page.insert_text((72, 72), text)
    document.save(path)
    document.close()


def test_process_pdf_exports_complete_mult_page_document(tmp_path):
    pdf_path = tmp_path / "sample.pdf"
    output_dir = tmp_path / "nested" / "output"
    create_pdf(pdf_path, ["First page", "", "Third page"])

    document, output_files = process_pdf(pdf_path, output_dir)

    assert document.filename == "sample.pdf"
    assert document.total_pages == 3
    assert [page.page_number for page in document.pages] == [1, 2, 3]
    assert "First page" in document.pages[0].cleaned_text
    assert document.pages[1].cleaned_text == ""
    assert "Third page" in document.pages[2].cleaned_text

    assert output_files["json"].exists()
    assert output_files["txt"].exists()

    json_data = json.loads(output_files["json"].read_text(encoding="utf-8"))
    txt_data = output_files["txt"].read_text(encoding="utf-8")
    assert json_data["total_pages"] == 3
    assert [page["page_number"] for page in json_data["pages"]] == [1, 2, 3]
    assert "第 2 页" in txt_data
    assert txt_data.index("第 1 页") < txt_data.index("第 2 页") < txt_data.index("第 3 页")


def test_process_pdf_uses_pdf_filename_for_chinese_output_names(tmp_path):
    pdf_path = tmp_path / "中文资料.pdf"
    create_pdf(pdf_path, ["Chinese content"])

    document, output_files = process_pdf(pdf_path, tmp_path / "output")

    assert document.filename == "中文资料.pdf"
    assert output_files["json"].name == "中文资料.json"
    assert output_files["txt"].name == "中文资料.txt"
    json_data = json.loads(output_files["json"].read_text(encoding="utf-8"))
    assert json_data["filename"] == "中文资料.pdf"


def test_process_pdf_rejects_pdf_without_extractable_text(tmp_path):
    pdf_path = tmp_path / "empty.pdf"
    create_pdf(pdf_path, ["", ""])

    with pytest.raises(PDFDocumentError, match="没有可提取的文本内容"):
        process_pdf(pdf_path, tmp_path / "output")

    assert not (tmp_path / "output").exists()


def test_process_pdf_reports_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="PDF 文件不存在"):
        process_pdf(tmp_path / "missing.pdf", tmp_path / "output")


def test_process_pdf_reports_invalid_pdf(tmp_path):
    invalid_pdf = tmp_path / "invalid.pdf"
    invalid_pdf.write_text("not a pdf", encoding="utf-8")

    with pytest.raises(PDFDocumentError):
        process_pdf(invalid_pdf, tmp_path / "output")

    assert not (tmp_path / "output").exists()

