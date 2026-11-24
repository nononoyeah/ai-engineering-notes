
# PDF 文档解析模块

## 1. 模块简介

本模块用于读取 PDF 文件并提取逐页文本内容。

当前支持：
- PDF 文件存在性检查。
- PDF 文件有效性检查。
- PDF 逐页文本提取。
- 保留原始页面顺序和页码。
- 保留空白页记录。
- 对全文无可提取文本的 PDF 返回明确异常。
- 对单页提取失败提供页码和错误原因。

暂不支持：
- 图片 OCR 文字识别。
- PDF 文本清洗。
- 文本分块（Chunk）。

## 2. 文件结构

```text
document_parser/
├── __init__.py
├── models.py
├── pdf_parser.py
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

## 4. 调用示例

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
        print(page.text)

except FileNotFoundError as exc:
    print(f"文件不存在：{exc}")

except PDFDocumentError as exc:
    print(f"PDF 解析失败：{exc}")
```

## 5. 异常说明

| 异常 | 触发场景 |
|---|---|
| FileNotFoundError | PDF 文件不存在 |
| PDFDocumentError | 文件不是有效 PDF、无法读取 PDF、页面提取失败或全文无可提取文本 |

## 6. 测试

在项目根目录执行：

```powershell
python -m pytest tests/test_pdf_parser.py -v
```

## 7. 当前功能限制

1. 目前只提取 PDF 中可直接读取的文本。
2. 扫描件或纯图片 PDF 暂不支持 OCR。
3. 当前返回原始文本，尚未进行文本清洗。
4. 暂未实现 TXT 和 JSON 文件导出。
