# Tasks

## 1. 依赖与数据结构

- [x] 1.1 在 `backend/requirements.txt` 中加入 `markdown-it-py`；通过执行 `python -m pip install -r backend/requirements.txt` 和 `python -c "from markdown_it import MarkdownIt; MarkdownIt('commonmark')"` 验证依赖可安装、可导入。
- [x] 1.2 在 `models.py` 中为 `PageContent` 增加 `heading_path`（默认空字符串）和 `heading_level`（默认 0），为 `DocumentContent` 增加 `source_type`（默认 `"pdf"`）；通过在 `tests/test_models.py` 中补充用例验证默认值和 Markdown 字段赋值，并通过执行 `python -m pytest tests/test_models.py -v` 验证通过。

## 2. Markdown 文本清洗

- [x] 2.1 在 `text_cleaner.py` 中实现 `clean_markdown_text(lines, start, end, code_lines)`：非代码行去除行尾空白、连续空行压缩为一个空行、去除首尾空白行，代码行原样保留；通过在 `tests/test_text_cleaner.py` 中补充用例覆盖行尾空白、连续空行、代码行的缩进与多空格与空行、列表缩进和表格行，并通过执行 `python -m pytest tests/test_text_cleaner.py -v` 验证通过。
- [x] 2.2 在 `backend/app/document_parser/README.md` 的文本清洗部分记录 Markdown 清洗规则及其与 PDF 清洗的区别；通过对照 `tests/test_text_cleaner.py` 中的用例核对文档描述与实际行为一致。

## 3. Markdown 解析

- [x] 3.1 新增 `markdown_parser.py`，实现 `MarkdownDocumentError` 和 `extract_markdown_content()` 的读取与校验：以 `utf-8-sig` 读取并统一换行符，文件不存在抛出 `FileNotFoundError`，路径不是文件、读取失败、无法按 UTF-8 解码、没有可提取文本时抛出 `MarkdownDocumentError`；通过新增 `tests/test_markdown_parser.py` 并覆盖不存在的文件、目录路径、非 UTF-8 字节、空文件、纯空白文件、带 BOM 和 CRLF 的文件，验证错误信息和读取结果符合预期。
- [x] 3.2 实现 Markdown 标题切分：使用 `MarkdownIt("commonmark")` 解析全文一次，以嵌套层级为 0 的 `heading_open` token 确定节的起始行、层级和标题文本，借助上级标题栈生成标题路径，前言节层级为 0 且纯空白前言省略，front matter 范围内的标题不参与切分；通过在 `tests/test_markdown_parser.py` 中补充用例，覆盖多级标题的顺序与标题路径、各节原文拼接等于全文、无标题文档、层级跳跃、只有标题行的节、代码块内的 `#`、引用和列表内的标题、front matter、未闭合围栏，验证切分结果。
- [x] 3.3 在解析流程中集成清洗：从同一次解析中取 `fence`、`code_block`、`html_block` 的行范围作为代码行，对每个节调用 `clean_markdown_text()`，生成 `PageContent` 并返回 `source_type` 为 `"markdown"` 的 `DocumentContent`；通过在 `tests/test_markdown_parser.py` 中补充用例，验证节序号从 1 连续、节总数正确、`text` 为原文、`cleaned_text` 中代码块内容保持不变。
- [x] 3.4 在 `backend/app/document_parser/README.md` 中新增 Markdown 解析说明，包括支持的扩展名、节的定义、标题路径格式、读取编码、异常说明和调用示例；通过按文档示例调用 `extract_markdown_content()` 验证说明与实际接口一致。

## 4. 导出与统一入口

- [x] 4.1 调整 `exporters.py`：JSON 顶层增加 `source_type`，每段增加 `heading_path` 和 `heading_level`；TXT 分隔标记对 Markdown 显示 `第 N 节` 和标题路径（前言节显示“无标题”），PDF 保持原有页码标记；通过在 `tests/test_exporters.py` 中补充用例，验证 Markdown 的 JSON 字段与 TXT 标记、PDF 的 JSON 标明来源类型且 TXT 标记不变，并通过执行 `python -m pytest tests/test_exporters.py -v` 验证通过。
- [x] 4.2 在 `pipeline.py` 中新增 `UnsupportedFileTypeError` 和 `process_document()`，按小写扩展名分发 `.pdf`、`.md`、`.markdown`，不支持的类型在创建输出目录之前抛出异常；通过在 `tests/test_pipeline.py` 中补充用例，验证 Markdown 的端到端导出、`.MD` 和 `.markdown` 扩展名、PDF 结果与 `process_pdf()` 一致、不支持的类型和解析失败时不产生输出目录，并通过执行 `python -m pytest tests/test_pipeline.py -v` 验证通过。
- [x] 4.3 在 `backend/app/document_parser/README.md` 中新增统一入口 `process_document()` 的说明，包括分发规则、返回值和异常，并更新文件结构；通过按文档示例调用 `process_document()` 验证说明与实际接口一致。

## 5. 集成验证与项目文档

- [x] 5.1 在项目根目录执行 `python -m pytest -v`，验证全部测试通过且 PDF 相关用例无回归。
- [x] 5.2 更新项目 `README.md`：将 Markdown 文档解析移入已完成项，补充 `process_document()` 用法、输出字段说明、更新后的项目结构和测试命令；通过按 README 的步骤执行安装和测试命令，验证说明可复现。
- [x] 5.3 更新主规范 `openspec/specs/document-parsing/spec.md` 的 Purpose，使其覆盖 PDF 和 Markdown 文档；通过执行 `openspec validate document-parsing --type spec --strict` 验证通过。

## Workflow follow-up

- 实现完成并通过评审后归档该变更：`openspec archive implement-markdown-document-parser`。
- 归档后确认 delta 规范已合并进主规范 `document-parsing`。
