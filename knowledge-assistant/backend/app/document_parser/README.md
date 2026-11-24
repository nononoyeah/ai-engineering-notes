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