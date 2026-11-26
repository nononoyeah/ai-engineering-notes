import json
import os
import tempfile
from pathlib import Path

from backend.app.document_parser.models import DocumentContent


class ExportError(Exception):
    """文档导出失败。"""


def _write_text_atomically(path: Path, content: str, file_type: str) -> Path:
    """先写入同目录临时文件，再替换目标文件，避免留下半截目标文件。"""
    temp_path = None

    try:
        file_descriptor, temp_name = tempfile.mkstemp(
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
        )
        os.close(file_descriptor)
        temp_path = Path(temp_name)

        with temp_path.open("w", encoding="utf-8") as file:
            file.write(content)

        os.replace(temp_path, path)
        return path

    except OSError as exc:
        if temp_path is not None:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass
        raise ExportError(
            f"{file_type} 文件写入失败：{path}，原因：{exc}"
        ) from exc


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
        "source_type": document.source_type,
        "total_pages": document.total_pages,
        "pages": [
            {
                "page_number": page.page_number,
                "heading_path": page.heading_path,
                "heading_level": page.heading_level,
                "text": page.text,
                "cleaned_text": page.cleaned_text,
            }
            for page in document.pages
        ],
    }

    try:
        content = json.dumps(data, ensure_ascii=False, indent=4)
    except (TypeError, ValueError) as exc:
        raise ExportError(
            f"JSON 内容序列化失败：{path}，原因：{exc}"
        ) from exc

    return _write_text_atomically(path, content, "JSON")


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
        if document.source_type == "markdown":
            label = f"第 {page.page_number} 节  {page.heading_path or '无标题'}"
        else:
            label = f"第 {page.page_number} 页"

        sections.append(
            f"========== {label} ==========\n"
            f"{page.cleaned_text}"
        )

    content = "\n\n".join(sections)
    return _write_text_atomically(path, content, "TXT")


def export_document(
    document: DocumentContent,
    output_dir: str | Path,
) -> dict[str, Path]:
    """
    将文档解析结果同时导出为 TXT 和 JSON。

    自动创建输出目录，并根据原始文件名生成输出文件名。
    """
    directory = Path(output_dir)

    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ExportError(
            f"输出目录创建失败：{directory}，原因：{exc}"
        ) from exc

    filename = Path(document.filename).stem
    json_path = directory / f"{filename}.json"
    txt_path = directory / f"{filename}.txt"

    export_to_json(document, json_path)
    export_to_txt(document, txt_path)

    return {
        "json": json_path,
        "txt": txt_path,
    }

