import json
import pytest
from pathlib import Path
from unittest.mock import patch

from backend.app.document_parser.exporters import ExportError
from backend.app.document_parser.exporters import (
    export_to_json,
    export_to_txt,
    export_document,
)
from backend.app.document_parser.models import DocumentContent, PageContent


def test_export_to_json_preserves_structure_and_chinese(tmp_path):
    document = DocumentContent(
        filename="测试文档.pdf",
        total_pages=2,
        pages=[
            PageContent(
                page_number=1,
                text="  第一页 原始内容  ",
                cleaned_text="第一页 原始内容",
            ),
            PageContent(
                page_number=2,
                text="第二页原始内容",
                cleaned_text="第二页原始内容",
            ),
        ],
    )

    output_path = tmp_path / "测试文档.json"

    result = export_to_json(document, output_path)

    assert result == output_path
    assert output_path.exists()

    content = output_path.read_text(encoding="utf-8")
    data = json.loads(content)

    assert data["filename"] == "测试文档.pdf"
    assert data["total_pages"] == 2
    assert len(data["pages"]) == 2

    assert data["pages"][0]["page_number"] == 1
    assert data["pages"][0]["text"] == "  第一页 原始内容  "
    assert data["pages"][0]["cleaned_text"] == "第一页 原始内容"

    assert data["pages"][1]["page_number"] == 2
    assert data["pages"][1]["text"] == "第二页原始内容"


def test_export_to_txt_preserves_page_order_and_markers(tmp_path):
    document = DocumentContent(
        filename="测试文档.pdf",
        total_pages=3,
        pages=[
            PageContent(
                page_number=1,
                text="第一页原始内容",
                cleaned_text="第一页清洗内容",
            ),
            PageContent(
                page_number=2,
                text="",
                cleaned_text="",
            ),
            PageContent(
                page_number=3,
                text="第三页原始内容",
                cleaned_text="第三页清洗内容",
            ),
        ],
    )

    output_path = tmp_path / "测试文档.txt"

    result = export_to_txt(document, output_path)

    assert result == output_path
    assert output_path.exists()

    content = output_path.read_text(encoding="utf-8")

    assert "第 1 页" in content
    assert "第 2 页" in content
    assert "第 3 页" in content

    assert content.index("第 1 页") < content.index("第 2 页")
    assert content.index("第 2 页") < content.index("第 3 页")

    assert "第一页清洗内容" in content
    assert "第三页清洗内容" in content
    assert "第一页原始内容" not in content


def test_export_document_creates_directory_and_both_files(tmp_path):
    document = DocumentContent(
        filename="项目资料.pdf",
        total_pages=2,
        pages=[
            PageContent(
                page_number=1,
                text="第一页原始内容",
                cleaned_text="第一页清洗内容",
            ),
            PageContent(
                page_number=2,
                text="第二页原始内容",
                cleaned_text="第二页清洗内容",
            ),
        ],
    )

    output_dir = tmp_path / "nested" / "output"

    result = export_document(document, output_dir)

    assert output_dir.exists()
    assert result["json"].name == "项目资料.json"
    assert result["txt"].name == "项目资料.txt"
    assert result["json"].exists()
    assert result["txt"].exists()

    json_data = json.loads(result["json"].read_text(encoding="utf-8"))
    txt_content = result["txt"].read_text(encoding="utf-8")

    assert json_data["filename"] == "项目资料.pdf"
    assert "第一页清洗内容" in txt_content
    assert "第二页清洗内容" in txt_content


def test_export_document_reports_directory_creation_error(tmp_path):
    document = DocumentContent(
        filename="测试文档.pdf",
        total_pages=1,
        pages=[
            PageContent(
                page_number=1,
                text="测试内容",
                cleaned_text="测试内容",
            )
        ],
    )

    output_dir = tmp_path / "unavailable"

    with patch.object(
        Path,
        "mkdir",
        side_effect=OSError("模拟目录创建失败"),
    ):
        with pytest.raises(ExportError, match="输出目录创建失败"):
            export_document(document, output_dir)


def test_export_to_json_reports_write_error(tmp_path):
    document = DocumentContent(
        filename="测试文档.pdf",
        total_pages=1,
        pages=[
            PageContent(
                page_number=1,
                text="测试内容",
                cleaned_text="测试内容",
            )
        ],
    )

    output_path = tmp_path / "测试文档.json"

    with patch.object(
        Path,
        "open",
        side_effect=OSError("模拟文件写入失败"),
    ):
        with pytest.raises(ExportError, match="JSON 文件写入失败"):
            export_to_json(document, output_path)