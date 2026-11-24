import json

from backend.app.document_parser.exporters import export_to_json
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