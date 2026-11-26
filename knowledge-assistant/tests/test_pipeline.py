import json

import pymupdf
import pytest

from backend.app.document_parser.markdown_parser import MarkdownDocumentError
from backend.app.document_parser.pdf_parser import PDFDocumentError
from backend.app.document_parser.pipeline import (
    UnsupportedFileTypeError,
    process_document,
    process_pdf,
)


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


def test_process_document_processes_markdown_end_to_end(tmp_path):
    md_path = tmp_path / "笔记.md"
    md_path.write_text(
        "# 一级标题\n\n前言\n\n## 二级标题\n\n正文   \n\n```python\nx = 1\n```\n",
        encoding="utf-8",
    )
    output_dir = tmp_path / "output"

    document, output_files = process_document(md_path, output_dir)

    assert document.source_type == "markdown"
    assert document.total_pages == 2
    assert document.pages[1].heading_path == "一级标题 > 二级标题"

    assert output_files["json"].name == "笔记.json"
    assert output_files["txt"].name == "笔记.txt"

    json_data = json.loads(output_files["json"].read_text(encoding="utf-8"))
    txt_content = output_files["txt"].read_text(encoding="utf-8")

    assert json_data["source_type"] == "markdown"
    assert json_data["pages"][1]["heading_path"] == "一级标题 > 二级标题"
    assert "第 1 节" in txt_content
    assert "第 2 节  一级标题 > 二级标题" in txt_content
    assert "正文" in txt_content


def test_process_document_accepts_uppercase_and_markdown_extensions(tmp_path):
    upper_path = tmp_path / "NOTES.MD"
    upper_path.write_text("# 标题\n\n正文\n", encoding="utf-8")
    long_ext_path = tmp_path / "notes.markdown"
    long_ext_path.write_text("# 标题\n\n正文\n", encoding="utf-8")

    upper_result = process_document(upper_path, tmp_path / "out1")
    long_ext_result = process_document(long_ext_path, tmp_path / "out2")

    assert upper_result[0].source_type == "markdown"
    assert long_ext_result[0].source_type == "markdown"
    assert (tmp_path / "out1" / "NOTES.json").exists()
    assert (tmp_path / "out2" / "notes.json").exists()


def test_process_document_processes_pdf_like_process_pdf(tmp_path):
    pdf_path = tmp_path / "sample.pdf"
    create_pdf(pdf_path, ["First page", "Second page"])

    document, output_files = process_document(pdf_path, tmp_path / "output")
    reference, _ = process_pdf(pdf_path, tmp_path / "reference")

    assert document.source_type == "pdf"
    assert [page.cleaned_text for page in document.pages] == [
        page.cleaned_text for page in reference.pages
    ]
    assert output_files["json"].exists()
    assert output_files["txt"].exists()

    txt_content = output_files["txt"].read_text(encoding="utf-8")
    assert "第 1 页" in txt_content
    assert "第 2 页" in txt_content


def test_process_document_rejects_unsupported_type(tmp_path):
    txt_path = tmp_path / "资料.txt"
    txt_path.write_text("内容", encoding="utf-8")

    with pytest.raises(UnsupportedFileTypeError, match="不支持的文件类型"):
        process_document(txt_path, tmp_path / "output")

    assert not (tmp_path / "output").exists()


def test_process_document_does_not_export_when_markdown_parsing_fails(tmp_path):
    md_path = tmp_path / "blank.md"
    md_path.write_text(" \n\n", encoding="utf-8")

    with pytest.raises(MarkdownDocumentError, match="没有可提取的文本内容"):
        process_document(md_path, tmp_path / "output")

    assert not (tmp_path / "output").exists()

