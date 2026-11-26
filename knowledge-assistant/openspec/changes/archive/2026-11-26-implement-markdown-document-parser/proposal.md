# Proposal

## Why

个人知识库的文档来源除 PDF 外，还包括大量 Markdown 笔记和说明文档。当前解析链路只支持 PDF，Markdown 文件无法进入清洗与导出流程，后续文本分块也缺少可用的结构信息。

PDF 以页码作为结构锚点，Markdown 的对应物是标题。解析阶段按标题切分并保留标题路径，后续分块和引用溯源才能拿到与 PDF 页码同等粒度的输入。

## What Changes

- 新增 Markdown 文档解析能力：读取 `.md` / `.markdown` 文件，按顶层标题（H1–H6）切分为按原文顺序排列的节，每一节记录标题路径和标题层级。
- 新增 Markdown 文本清洗：保留 Markdown 语法，仅规范化代码块之外的空白；代码块内容原样保留。
- 新增统一处理入口 `process_document()`：按文件扩展名选择 PDF 或 Markdown 解析器，其他类型返回明确的错误。
- 扩展解析结果数据结构：新增来源类型，以及每一节的标题路径和标题层级；PDF 解析结果的行为保持不变。
- TXT 和 JSON 导出同时覆盖 Markdown 解析结果：TXT 分隔标记对 Markdown 显示节序号和标题路径；JSON 增加来源类型和标题字段。
- 引入直接依赖 `markdown-it-py`，用于定位标题和代码块。
- 补充 Markdown 解析与统一入口的自动化测试，同步更新模块 README、项目 README 和 `document-parsing` 规范。

本次不涉及：

- 按长度做二次切分、重叠（Overlap）和过短节合并等文本分块规则。
- 将 Markdown 去标记转换为纯文本。
- 将 front matter 字段解析为元数据。
- 图片提取，以及非 UTF-8 编码的回退解码。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `document-parsing`: 新增 Markdown 文件读取、Markdown 标题切分、Markdown 文本清洗、按文件类型选择解析器四项要求；TXT 文件输出、JSON 文件输出两项要求扩展为同时覆盖 Markdown 解析结果。

## Impact

- **Backend**：新增 `markdown_parser.py`；`models.py`、`text_cleaner.py`、`exporters.py`、`pipeline.py` 为增量修改；`pdf_parser.py`、`process_pdf()` 和现有 PDF 行为不变。
- **Tests**：新增 `tests/test_markdown_parser.py`，扩展 `tests/test_text_cleaner.py`、`tests/test_exporters.py`、`tests/test_pipeline.py`；现有测试无需修改即可通过。
- **Dependencies**：新增直接依赖 `markdown-it-py`。当前环境中它已作为 `rich` 的间接依赖存在，但仍需显式写入 `backend/requirements.txt`。
- **File Output**：PDF 的 TXT 输出不变；JSON 新增 `source_type` 以及每一页的 `heading_path`、`heading_level`，属于增量兼容变更。Markdown 的输出文件命名规则与 PDF 相同。
- **Future Integration**：每个 Markdown 节携带标题路径和层级，供后续文本分块（过短节合并、过长节二次切分）和引用溯源使用。
