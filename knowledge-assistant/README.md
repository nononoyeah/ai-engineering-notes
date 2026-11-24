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

