# Personal Knowledge Base Assistant

个人知识库 AI 助手项目。当前处于基础能力建设阶段，优先实现可独立验证、可复用的文档处理能力，再逐步扩展到 RAG。

## 当前项目进度

已完成 PDF 和 Markdown 文档解析模块的基础实现：

- PDF 文件存在性和有效性检查
- 按原始页序逐页提取文本，页码从 1 开始
- 保留空白页
- Markdown 文件读取（`.md` / `.markdown`，UTF-8，兼容 BOM 和 Windows 换行符）
- Markdown 按顶层标题（H1–H6）切分为节，记录标题路径和标题层级
- 保留原始文本并生成基础清洗文本
- 导出 UTF-8 TXT 和 JSON
- 通过统一入口按文件类型完成解析与导出

当前尚未实现：

- 文本分块（Chunk）
- Embedding
- PostgreSQL / pgvector 向量存储
- 向量检索、RAG 问答和引用展示
- Web / Streamlit 交互界面

## 技术栈

- Python 3.12
- PyMuPDF：PDF 文本读取
- markdown-it-py：Markdown 标题和代码块定位
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
│   │       ├── markdown_parser.py
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

## 使用文档解析功能

统一入口 `process_document()` 按文件扩展名自动分发：`.pdf` 走 PDF 解析，`.md` 和 `.markdown` 走 Markdown 解析（不区分大小写）。

在项目根目录创建或运行 Python 脚本：

```python
from backend.app.document_parser.pipeline import process_document

document, output_files = process_document(
    file_path="你的文档.pdf",  # 或 "你的笔记.md"
    output_dir="output",
)

print(f"文件名：{document.filename}")
print(f"来源类型：{document.source_type}")
print(f"总段数：{document.total_pages}")  # PDF 为页数，Markdown 为节数
print(f"JSON：{output_files['json']}")
print(f"TXT：{output_files['txt']}")
```

`process_document()` 会依次完成文件校验、解析（PDF 逐页提取 / Markdown 按标题切分）、文本清洗，以及 TXT / JSON 导出。

只处理 PDF 时也可以使用 `process_pdf()`，行为与 `process_document()` 的 PDF 分支一致。

### 输出说明

- JSON：保存文件名、来源类型、总段数，以及每段的段序号、原始文本和清洗后文本；Markdown 的每段还包含标题路径和标题层级。
- TXT：按原始顺序输出清洗后的文本：PDF 使用页码分隔标记，Markdown 使用节序号和标题路径分隔标记。
- 默认输出目录为项目根目录下的 `output`。
- `output` 中的运行产物不应提交到 Git。

## 运行测试

在项目根目录执行全部自动化测试：

```powershell
python -m pytest -v
```

只运行文档解析模块相关测试：

```powershell
python -m pytest tests/test_models.py tests/test_pdf_parser.py tests/test_markdown_parser.py tests/test_text_cleaner.py tests/test_exporters.py tests/test_pipeline.py -v
```

## 当前功能限制

- 目前只提取 PDF 中可直接读取的文本。
- 扫描件或纯图片 PDF 暂不支持 OCR。
- 当前只进行基础格式清洗，不进行语义纠错。
- Markdown 只识别标准 Markdown 标题（加粗行不当作标题），front matter 不解析为元数据，也不做非 UTF-8 编码的回退解码。
- 暂未实现文本分块（Chunk）。
- 暂未实现 Embedding、向量数据库和 RAG 问答。
- PDF 复杂排版、表格和跨页段落暂不保证还原。

## 开发约定

- 优先使用官方文档和项目实践学习。
- 每项能力先实现、再测试、再记录文档。
- 不将公司、客户或内部业务资料放入公开仓库；公开演示仅使用公开或自行构造的测试资料。

