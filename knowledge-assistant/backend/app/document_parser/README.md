# 文档解析模块

## 1. 模块简介

本模块用于读取 PDF 和 Markdown 文件，提取文本，并对提取的文本进行基础格式清洗。

当前支持：

- PDF 文件存在性检查。
- PDF 文件有效性检查。
- PDF 逐页文本提取。
- 保留原始页面顺序和页码。
- 保留空白页记录。
- Markdown 文件读取（`.md` / `.markdown`，UTF-8，兼容 BOM 和 Windows 换行符）。
- Markdown 按顶层标题（H1–H6）切分为节，记录标题路径和标题层级。
- 对全文无可提取文本的 PDF 和 Markdown 返回明确异常。
- 对单页提取失败提供页码和错误原因。
- 保留原始文本，并单独保存清洗后的文本。
- 对每页（PDF）/ 每节（Markdown）文本独立执行基础格式清洗。

暂不支持：

- 图片 OCR 文字识别。
- 文本分块（Chunk）。
- 复杂 PDF 版面重建。
- Markdown front matter 字段解析为元数据。
- 非 UTF-8 编码的 Markdown 回退解码。

## 2. 文件结构

```text
document_parser/
├── __init__.py
├── models.py
├── pdf_parser.py
├── markdown_parser.py
├── text_cleaner.py
├── exporters.py
├── pipeline.py
└── README.md
```

## 3. 解析结果结构

### DocumentContent

| 字段 | 类型 | 说明 |
|---|---|---|
| filename | str | 文档文件名 |
| source_type | str | 来源类型：`"pdf"` 或 `"markdown"` |
| total_pages | int | PDF 为总页数，Markdown 为节总数 |
| pages | list[PageContent] | 逐页（PDF）或逐节（Markdown）解析结果 |

### PageContent

| 字段 | 类型 | 说明 |
|---|---|---|
| page_number | int | PDF 为页码，Markdown 为节序号，从 1 开始 |
| text | str | 当前页 / 节的原始文本 |
| cleaned_text | str | 当前页 / 节清洗后的文本 |
| heading_path | str | Markdown 节的标题路径，如 `一级 > 二级`；前言节和 PDF 为空字符串 |
| heading_level | int | Markdown 节的标题层级（1–6），前言节为 0；PDF 为 0 |

## 4. 文本清洗规则

文本清洗由 `text_cleaner.py` 负责，PDF 与 Markdown 使用不同的清洗规则。

### 4.1 PDF 文本清洗

由 `clean_text()` 函数负责，对每一页独立执行。当前处理规则：

1. 统一 Windows 和旧式换行符为 `\n`。
2. 去除文本首尾空白。
3. 将连续空格和制表符合并为一个空格。
4. 将连续空行压缩为一个空行。
5. 保留段落和列表的基本换行结构。

### 4.2 Markdown 文本清洗

由 `clean_markdown_text()` 函数负责，对每一个节独立执行。当前处理规则：

1. 去除非代码行的行尾空白。
2. 将连续空行压缩为一个空行。
3. 去除节首尾的空白行。
4. 代码块（围栏代码块、缩进代码块、原始 HTML 块）内的行原样保留。

与 PDF 清洗的区别：Markdown 的缩进和行内连续空格有语法含义（嵌套列表、代码缩进），因此不合并行内空格，只处理行尾空白和空行，并且代码块整体不参与清洗。换行符统一在 Markdown 读取阶段完成。

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

## 5. Markdown 解析

### 5.1 支持的文件

- 扩展名 `.md` 和 `.markdown`（统一入口中不区分大小写）。
- UTF-8 编码，兼容 BOM 和 Windows 换行符；换行符统一为 `\n` 后再解析。
- 非 UTF-8 内容返回明确的读取失败错误，不做回退解码。

### 5.2 标题切分

`markdown_parser.py` 的 `extract_markdown_content()` 负责读取和切分：

- 按顶层标题（H1–H6，含 Setext 写法）切分为节，每节从标题行开始，到下一个任意层级标题之前结束。
- 引用块和列表内的标题不作为切分边界；代码块内的 `#` 行不识别为标题。
- 文件开头的 YAML front matter（`---` 包围的元数据块）不识别为标题，原样保留在前言节中。
- 第一个标题之前的内容作为前言节，层级为 0，标题路径为空；纯空白的前言省略。
- 每节记录标题路径（上级标题用 ` > ` 连接，如 `一级 > 二级 > 三级`）和标题层级。
- 各节原始文本按顺序拼接等于全文（除换行符统一外不丢失、不重复内容）。

### 5.3 调用示例

在项目根目录执行以下代码：

```python
from backend.app.document_parser.markdown_parser import (
    extract_markdown_content,
    MarkdownDocumentError,
)

try:
    result = extract_markdown_content("笔记.md")

    print(f"文件名：{result.filename}")
    print(f"节数：{result.total_pages}")

    for section in result.pages:
        print(f"\n第 {section.page_number} 节：")
        print(f"标题路径：{section.heading_path or '（无标题）'}")
        print(f"标题层级：{section.heading_level}")
        print(section.cleaned_text)

except FileNotFoundError as exc:
    print(f"文件不存在：{exc}")

except MarkdownDocumentError as exc:
    print(f"Markdown 解析失败：{exc}")
```

## 6. PDF 调用示例

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

## 7. 异常说明

| 异常 | 触发场景 |
|---|---|
| FileNotFoundError | 文件不存在（PDF 或 Markdown） |
| PDFDocumentError | 文件不是有效 PDF、无法读取 PDF、页面提取失败或全文无可提取文本 |
| MarkdownDocumentError | Markdown 路径不是文件、读取或解码失败，或全文没有可提取文本 |

## 8. 测试

在项目根目录执行：

```powershell
python -m pytest tests/test_pdf_parser.py tests/test_markdown_parser.py tests/test_text_cleaner.py -v
```

## 9. 当前功能限制

1. 目前只提取 PDF 中可直接读取的文本。
2. 扫描件或纯图片 PDF 暂不支持 OCR。
3. 当前只进行基础格式清洗，不进行语义纠错。
4. Markdown 只把标准 Markdown 标题（含 Setext 写法）识别为节，不把加粗行当作标题。
5. Markdown front matter 只做防误切处理，不解析为元数据；仅含 front matter 的文件会被视为一个有效的前言节。
6. Markdown 不做非 UTF-8 编码的回退解码。
7. 暂未实现文本分块（Chunk）。



## 10. 文件导出

### 10.1 支持的导出格式

模块支持将 PDF 和 Markdown 的解析结果导出为 JSON 和 TXT：

| 格式 | 导出内容 | 用途 |
|---|---|---|
| JSON | 文件名、来源类型、总段数，以及每段的段序号、标题路径（Markdown）、标题层级（Markdown）、原始文本和清洗后文本 | 保留完整解析信息，便于程序读取 |
| TXT | 逐段清洗后的文本及分隔标记：PDF 为页码标记，Markdown 为节序号和标题路径标记 | 便于阅读及后续知识库文本处理 |

### 10.2 导出接口

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

按照原始顺序导出清洗后的文本。PDF 每页使用 `========== 第 N 页 ==========` 分隔；Markdown 每节使用 `========== 第 N 节  标题路径 ==========` 分隔，前言节显示 `无标题`。

**统一导出：**

```python
export_document(document, output_dir)
```

同时生成 JSON 和 TXT 文件，自动创建输出目录，并根据原始文件名生成输出文件名。

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

### 10.3 完整调用示例

```python
from backend.app.document_parser.pdf_parser import extract_pdf_content
from backend.app.document_parser.exporters import export_document

document = extract_pdf_content("example.pdf")

result = export_document(document, "output")

print("JSON 文件：", result["json"])
print("TXT 文件：", result["txt"])
```

### 10.4 异常处理

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



## 11. 统一处理入口

`pipeline.py` 提供两个统一入口：`process_document()` 按文件扩展名自动分发，`process_pdf()` 仅处理 PDF。

### 11.1 process_document()

按扩展名（不区分大小写）选择解析器：`.pdf` 走 PDF 解析，`.md` 和 `.markdown` 走 Markdown 解析。

```python
from backend.app.document_parser.pipeline import process_document

document, output_files = process_document(
    file_path="笔记.md",
    output_dir="output",
)

print(document.filename)
print(document.total_pages)
print(output_files["json"])
print(output_files["txt"])
```

执行顺序：

1. 按扩展名选择解析器；扩展名不在支持范围时抛出 `UnsupportedFileTypeError`，不会创建输出目录。
2. 调用对应的解析函数完成读取、切分 / 逐页提取和文本清洗。
3. 得到完整的 `DocumentContent`。
4. 调用 `export_document()` 导出 JSON 和 TXT。
5. 返回解析结果和两个输出文件路径。

返回值：

- `document`：`DocumentContent` 对象，包含文件名、来源类型、总段数和逐段原始/清洗文本。
- `output_files`：字典，包含 `json` 和 `txt` 两个 `Path` 路径。

异常沿用底层模块定义：文件不存在时抛出 `FileNotFoundError`；扩展名不受支持时抛出 `UnsupportedFileTypeError`；PDF 无效、读取失败或没有可提取文本时抛出 `PDFDocumentError`；Markdown 路径不是文件、读取失败或没有可提取文本时抛出 `MarkdownDocumentError`；导出失败时抛出 `ExportError`。

统一入口不会吞掉异常，也不会在解析失败时启动导出。

### 11.2 process_pdf()

只处理 PDF，行为与 `process_document()` 的 PDF 分支一致：

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
