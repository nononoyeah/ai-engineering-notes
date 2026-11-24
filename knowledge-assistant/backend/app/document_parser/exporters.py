import json
from pathlib import Path

from backend.app.document_parser.models import DocumentContent


def export_to_json(
    document: DocumentContent,
    output_path: str | Path,
) -> Path:
    """
    将文档解析结果导出为 JSON 文件。

    包含文件名、总页数、逐页原始文本和清洗后文本。
    """
    path = Path(output_path)

    data = {
        "filename": document.filename,
        "total_pages": document.total_pages,
        "pages": [
            {
                "page_number": page.page_number,
                "text": page.text,
                "cleaned_text": page.cleaned_text,
            }
            for page in document.pages
        ],
    }

    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

    return path