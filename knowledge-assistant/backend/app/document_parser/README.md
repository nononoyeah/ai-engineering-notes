# PDF 文档解析模块

## 1. 模块简介

本模块用于读取 PDF 文件、提取逐页文本，并对提取的文本进行基础格式清洗。

当前支持：

- PDF 文件存在性检查。
- PDF 文件有效性检查。
- PDF 逐页文本提取。
- 保留原始页面顺序和页码。
- 保留空白页记录。
- 对全文无可提取文本的 PDF 返回明确异常。
- 对单页提取失败提供页码和错误原因。
- 保留原始文本，并单独保存清洗后的文本。
- 对每页文本独立执行基础格式清洗。

暂不支持：

- 图片 OCR 文字识别。
- 文本分块（Chunk）。
- 复杂 PDF 版面重建。

## 2. 文件结构

```text
document_parser/
├── __init__.py
├── models.py
├── pdf_parser.py
├── text_cleaner.py
└── README.md
```

## 3. 解析结果结构

### DocumentContent

| 字段 | 类型 | 说明 |
|---|---|---|
| filename | str | PDF 文件名 |
| total_pages | int | PDF 总页数 |
| pages | list[PageContent] | 逐页解析结果 |

### PageContent

| 字段 | 类型 | 说明 |
|---|---|---|
| page_number | int | 页码，从 1 开始 |
| text | str | 当前页提取的原始文本 |
| cleaned_text | str | 当前页清洗后的文本 |

## 4. 文本清洗规则

文本清洗由 `text_cleaner.py` 中的 `clean_text()` 函数负责。

当前处理规则：

1. 统一 Windows 和旧式换行符为 `\n`。
2. 去除文本首尾空白。
3. 将连续空格和制表符合并为一个空格。
4. 将连续空行压缩为一个空行。
5. 保留段落和列表的基本换行结构。

### 原始文本与清洗文本

清洗不会覆盖原始文本：

- `text`：保存 PDF 提取的原始文本。
- `cleaned_text`：保存清洗后的文本。

两者分别存储，方便后续调试、对比和文本处理。

### 适用边界

当前清洗主要针对空格、制表符和多余空行等基础格式噪声。

暂不处理：

- OCR 识别及 OCR 错误纠正。
- 错误断句和语义纠错。
- 页眉、页脚及水印的智能识别与删除。
- 多栏排版和复杂表格的结构重建。
- 文本分块及语义切分。

## 5. 调用示例

在项目根目录执行以下代码：

```python
from backend.app.document_parser.pdf_parser import (
    extract_pdf_content,
    PDFDocumentError,
)

pdf_path = "example.pdf"

try:
    result = extract_pdf_content(pdf_path)

    print(f"文件名：{result.filename}")
    print(f"总页数：{result.total_pages}")

    for page in result.pages:
        print(f"\n第 {page.page_number} 页：")

        print("原始文本：")
        print(page.text)

        print("清洗后文本：")
        print(page.cleaned_text)

except FileNotFoundError as exc:
    print(f"文件不存在：{exc}")

except PDFDocumentError as exc:
    print(f"PDF 解析失败：{exc}")
```

## 6. 异常说明

| 异常 | 触发场景 |
|---|---|
| FileNotFoundError | PDF 文件不存在 |
| PDFDocumentError | 文件不是有效 PDF、无法读取 PDF、页面提取失败或全文无可提取文本 |

## 7. 测试

在项目根目录执行：

```powershell
python -m pytest tests/test_pdf_parser.py tests/test_text_cleaner.py -v
```

## 8. 当前功能限制

1. 目前只提取 PDF 中可直接读取的文本。
2. 扫描件或纯图片 PDF 暂不支持 OCR。
3. 当前只进行基础格式清洗，不进行语义纠错。
4. 暂未实现 TXT 和 JSON 文件导出。
5. 暂未实现文本分块（Chunk）。



## 9. 文件导出

### 9.1 支持的导出格式

模块支持将 PDF 解析结果导出为 JSON 和 TXT：

| 格式 | 导出内容 | 用途 |
|---|---|---|
| JSON | 文件名、总页数、逐页页码、原始文本、清洗后文本 | 保留完整解析信息，便于程序读取 |
| TXT | 逐页清洗后的文本及页码分隔标记 | 便于阅读及后续知识库文本处理 |

### 9.2 导出接口

导出模块位于 `exporters.py`。

**JSON 导出：**

```python
export_to_json(document, output_path)
```

将解析结果导出为 JSON 文件，使用 UTF-8 编码并保留中文。

**TXT 导出：**

```python
export_to_txt(document, output_path)
```

按照原始页序导出清洗后的文本，每页使用页码标记分隔。

**统一导出：**

```python
export_document(document, output_dir)
```

同时生成 JSON 和 TXT 文件，自动创建输出目录，并根据原始 PDF 文件名生成文件名。

例如，原始文件为 `项目资料.pdf`，输出目录为 `output/`，则生成：

```text
output/
├── 项目资料.json
└── 项目资料.txt
```

统一导出接口返回包含两个文件路径的字典：

```python
{
    "json": json_path,
    "txt": txt_path
}
```

### 9.3 完整调用示例

```python
from backend.app.document_parser.pdf_parser import extract_pdf_content
from backend.app.document_parser.exporters import export_document

document = extract_pdf_content("example.pdf")

result = export_document(document, "output")

print("JSON 文件：", result["json"])
print("TXT 文件：", result["txt"])
```

### 9.4 异常处理

导出失败时抛出 `ExportError`，目前覆盖：

- 输出目录创建失败。
- JSON 文件写入失败。
- TXT 文件写入失败。

调用方可以统一捕获：

```python
from backend.app.document_parser.exporters import (
    export_document,
    ExportError,
)

try:
    result = export_document(document, "output")
except ExportError as exc:
    print(f"文档导出失败：{exc}")
```

注意：`export_to_json` 和 `export_to_txt` 是底层独立导出接口，不负责自动创建父目录；需要自动创建目录时，建议使用 `export_document`。



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
