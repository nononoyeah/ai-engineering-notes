$ErrorActionPreference = "Stop"

# 必须从 knowledge-assistant 项目根目录执行
$root = (Get-Location).Path
$parserDir = Join-Path $root "backend\app\document_parser"
$testsDir = Join-Path $root "tests"

if (-not (Test-Path (Join-Path $root "backend\requirements.txt"))) {
    throw "当前目录看起来不是 knowledge-assistant 项目根目录。请先 cd 到项目根目录再执行。"
}

New-Item -ItemType Directory -Force -Path $parserDir | Out-Null
New-Item -ItemType Directory -Force -Path $testsDir | Out-Null

$pipeline = @'
from pathlib import Path

from backend.app.document_parser.exporters import export_document
from backend.app.document_parser.models import DocumentContent
from backend.app.document_parser.pdf_parser import extract_pdf_content


def process_pdf(
    pdf_path: str | Path,
    output_dir: str | Path = "output",
) -> tuple[DocumentContent, dict[str, Path]]:
    """
    完成 PDF 解析、逐页文本清洗和 TXT/JSON 导出。

    Args:
        pdf_path: 输入 PDF 文件路径。
        output_dir: 导出目录，默认为项目根目录下的 output。

    Returns:
        (document, output_files)
        document 为完整的逐页解析结果；
        output_files 包含 json、txt 两种格式的导出路径。

    Raises:
        FileNotFoundError: 输入文件不存在。
        PDFDocumentError: PDF 无效、无法读取或没有可提取文本。
        ExportError: 输出目录创建或文件导出失败。
    """
    document = extract_pdf_content(pdf_path)
    output_files = export_document(document, output_dir)
    return document, output_files

'@
Set-Content -Path (Join-Path $parserDir "pipeline.py") -Value $pipeline -Encoding utf8

$exporters = @'
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
        sections.append(
            f"========== 第 {page.page_number} 页 ==========\n"
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

'@
Set-Content -Path (Join-Path $parserDir "exporters.py") -Value $exporters -Encoding utf8

$testPipeline = @'
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

'@
Set-Content -Path (Join-Path $testsDir "test_pipeline.py") -Value $testPipeline -Encoding utf8

$rootReadme = @'
# Personal Knowledge Base Assistant

个人知识库 AI 助手项目。当前处于基础能力建设阶段，优先实现可独立验证、可复用的文档处理能力，再逐步扩展到 RAG。

## 当前项目进度

已完成 PDF 文档解析模块的基础实现：

- PDF 文件存在性和有效性检查
- 按原始页序逐页提取文本，页码从 1 开始
- 保留空白页
- 保留原始文本并生成基础清洗文本
- 导出 UTF-8 TXT 和 JSON
- 通过统一入口完成解析与导出

当前尚未实现：

- Markdown 文档解析
- 文本分块（Chunk）
- Embedding
- PostgreSQL / pgvector 向量存储
- 向量检索、RAG 问答和引用展示
- Web / Streamlit 交互界面

## 技术栈

- Python 3.12
- PyMuPDF：PDF 文本读取
- pytest：自动化测试

## 项目结构

```text
knowledge-assistant/
├── backend/
│   ├── app/
│   │   └── document_parser/
│   │       ├── __init__.py
│   │       ├── models.py
│   │       ├── pdf_parser.py
│   │       ├── text_cleaner.py
│   │       ├── exporters.py
│   │       ├── pipeline.py
│   │       └── README.md
│   └── requirements.txt
├── database/
├── docs/
├── frontend/
├── openspec/
├── output/
├── tests/
└── README.md
```

## 环境准备

在项目根目录执行。建议使用 Python 3.12，并在已激活的 Conda 环境中安装依赖：

```powershell
python -m pip install -r backend/requirements.txt
```

## 使用 PDF 解析功能

在项目根目录创建或运行 Python 脚本：

```python
from backend.app.document_parser.pipeline import process_pdf

document, output_files = process_pdf(
    pdf_path="你的 PDF 文件.pdf",
    output_dir="output",
)

print(f"文件名：{document.filename}")
print(f"总页数：{document.total_pages}")
print(f"JSON：{output_files['json']}")
print(f"TXT：{output_files['txt']}")
```

`process_pdf()` 会依次完成 PDF 校验、逐页文本提取、文本清洗，以及 TXT / JSON 导出。

### 输出说明

- JSON：保存文件名、总页数、逐页页码、原始文本和清洗后文本。
- TXT：按页码顺序输出清洗后的文本，并保留页面分隔标记。
- 默认输出目录为项目根目录下的 `output`。
- `output` 中的运行产物不应提交到 Git。

## 运行测试

在项目根目录执行全部自动化测试：

```powershell
python -m pytest -v
```

只运行 PDF 解析模块相关测试：

```powershell
python -m pytest tests/test_models.py tests/test_pdf_parser.py tests/test_text_cleaner.py tests/test_exporters.py tests/test_pipeline.py -v
```

## 当前功能限制

- 目前只提取 PDF 中可直接读取的文本。
- 扫描件或纯图片 PDF 暂不支持 OCR。
- 当前只进行基础格式清洗，不进行语义纠错。
- 暂未实现文本分块（Chunk）。
- 暂未实现 Embedding、向量数据库和 RAG 问答。
- PDF 复杂排版、表格和跨页段落暂不保证还原。

## 开发约定

- 优先使用官方文档和项目实践学习。
- 每项能力先实现、再测试、再记录文档。
- 不将公司、客户或内部业务资料放入公开仓库；公开演示仅使用公开或自行构造的测试资料。

'@
Set-Content -Path (Join-Path $root "README.md") -Value $rootReadme -Encoding utf8

$moduleReadmePath = Join-Path $parserDir "README.md"
$moduleReadme = Get-Content -Path $moduleReadmePath -Raw -Encoding utf8
if ($moduleReadme -notmatch "## 10\. 统一处理入口") {
    Add-Content -Path $moduleReadmePath -Value @'

## 10. 统一处理入口

除单独调用 PDF 读取和导出函数外，也可以使用 `pipeline.py` 中的 `process_pdf()` 一次完成整个处理流程。

```python
from backend.app.document_parser.pipeline import process_pdf

document, output_files = process_pdf(
    pdf_path="example.pdf",
    output_dir="output",
)

print(document.filename)
print(document.total_pages)
print(output_files["json"])
print(output_files["txt"])
```

`process_pdf()` 的执行顺序：

1. 调用 `extract_pdf_content()` 检查并读取 PDF。
2. 逐页提取文本，并在解析阶段完成基础文本清洗。
3. 得到完整的 `DocumentContent`。
4. 调用 `export_document()` 导出 JSON 和 TXT。
5. 返回解析结果和两个输出文件路径。

返回值：

- `document`：`DocumentContent` 对象，包含文件名、总页数和逐页原始/清洗文本。
- `output_files`：字典，包含 `json` 和 `txt` 两个 `Path` 路径。

异常沿用底层模块定义：文件不存在时抛出 `FileNotFoundError`；PDF 无效、读取失败或没有可提取文本时抛出 `PDFDocumentError`；导出失败时抛出 `ExportError`。

统一入口不会吞掉异常，也不会在 PDF 解析失败时启动导出。
'@ -Encoding utf8
}

Write-Host "阶段 5 文件已写入。请运行：python -m pytest -v" -ForegroundColor Green
