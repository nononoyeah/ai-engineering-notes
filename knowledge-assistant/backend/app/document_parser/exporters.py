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


def export_to_txt(
    document: DocumentContent,
    output_path: str | Path,
) -> Path:
    """
    将文档逐页文本导出为 TXT 文件。

    按照原始页序输出清洗后的文本，并使用页码分隔标记。
    """
    path = Path(output_path)

    sections = []

    for page in document.pages:
        sections.append(
            f"========== 第 {page.page_number} 页 ==========\n" f"{page.cleaned_text}"
        )

    content = "\n\n".join(sections)

    with path.open("w", encoding="utf-8") as file:
        file.write(content)

    return path
