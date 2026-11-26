# Design

## Context

动机见 `proposal.md` 的 Why，行为要求见 `specs/document-parsing/spec.md`。

当前解析链路只支持 PDF：

- `pdf_parser.py` 调用 PyMuPDF 逐页提取文本，结果为 `DocumentContent`（文件名、总页数、`pages` 列表），每一项是 `PageContent`（页码、原始文本、清洗文本）。
- `text_cleaner.py` 的 `clean_text()` 做空白清洗：合并连续空格和制表符、压缩连续空行、去首尾空白。
- `exporters.py` 把 `DocumentContent` 导出为 JSON 和 TXT（TXT 以 `========== 第 N 页 ==========` 分隔）。
- `pipeline.py` 的 `process_pdf()` 串联解析与导出。

探索阶段确认的约束：

- `clean_text()` 直接用于 Markdown 是破坏性的：嵌套列表的 4 空格缩进会变成 1 个空格，代码块内的 `x = "a    b"` 会变成 `x = "a b"`。
- 手写正则识别标题不可靠：代码块内的 `#` 行、引用和列表内的标题、列表项内缩进的围栏、Setext 标题、YAML front matter（`---` 包围的块会被 CommonMark 解析为二级标题）都会误判。
- 运行环境已有 `markdown-it-py` 2.2.0，但它只是 `rich` 的间接依赖，不在 `backend/requirements.txt` 中。
- 工作区现有的 Markdown 文件全部是 UTF-8，其中存在带 BOM 和使用 CRLF 换行的文件。

## Goals / Non-Goals

**Goals:**

- Markdown 与 PDF 的解析结果形状一致，导出器和统一入口无需区分文件类型即可完成导出。
- Markdown 的结构信息（标题路径、标题层级）在解析阶段一次给出，后续分块不必再次解析 Markdown。
- PDF 的解析结果、TXT 输出和现有测试保持不变。

**Non-Goals:**

- 不设计分块策略：长度阈值、Overlap、过短节合并、过长节二次切分都属于后续文本分块阶段。
- 不把 Markdown 转换为纯文本，不解析 front matter、图片或其他元数据。
- 不改动 `page_number`、`total_pages` 等现有字段名。

## Decisions

### 1. 复用现有解析结果结构，用带默认值的增量字段表达 Markdown 的节

**决定：** `PageContent` 新增 `heading_path: str = ""` 和 `heading_level: int = 0`；`DocumentContent` 新增 `source_type: str = "pdf"`，取值为 `"pdf"` 或 `"markdown"`。Markdown 的每个节对应一个 `PageContent`：`page_number` 为节序号（从 1 开始），`total_pages` 为节总数。`pdf_parser.py` 不改动，PDF 结果依靠字段默认值。

**原因：**

- 导出器对两种格式共用一套代码，现有 PDF 测试无需修改。
- PDF 的 JSON 输出只是增加字段，旧读取方不受影响。

**备选方案：**

- 为 Markdown 新建一套平行的数据结构和导出器：导出逻辑要复制一份，统一入口也要分支。
- 把 `pages` / `page_number` 改名为中性的 `sections`：所有 PDF 代码和测试都要跟着改，而分块阶段确定锚点语义后还要再改一次。

### 2. 在解析阶段按顶层标题切分，一级到六级全部作为边界

**决定：** 每个顶层标题（H1–H6，含 Setext 写法）开始一个新的节，节的内容从标题行起，到下一个任意层级的标题行之前为止。第一个标题之前的内容作为前言节（层级 0、标题路径为空）；前言只有空白时省略。每个节记录标题路径（上级标题用 ` > ` 连接）和标题层级。

**原因：**

- 合得起、拆不回。后续分块可以依据 `heading_level` 和 `heading_path` 合并过短的节，但解析阶段切粗了，分块就得重新解析 Markdown。
- 各节的原始文本按顺序拼接等于全文，除了换行符统一之外不丢失、不重复任何内容。
- 标题层级的取舍（按哪一级切）属于分块策略，不在解析阶段写死。

**备选方案：**

- 整份文档作为单页：标题结构要留给分块阶段再解析一次，TXT 和 JSON 对 Markdown 也只有“第 1 页”这种没有意义的信息。
- 只按固定层级切分（例如只按 H1 或 H2）：层级选择无法适配不同文档的写法。

### 3. 使用 markdown-it-py 定位标题和代码块，全文只解析一次

**决定：** 使用 `MarkdownIt("commonmark")`（CommonMark 预设）解析全文一次，从同一批 token 中取两类信息：

- 标题：类型为 `heading_open` 且嵌套层级为 0 的 token，取其起始行号、层级（`h1`–`h6`）和标题文本。标题文本取该行内联 token 的文本，空白折叠为单个空格。
- 代码块：类型为 `fence`、`code_block`、`html_block` 的 token，取其行范围。

**原因：**

- 解析器能正确处理 Context 中列出的全部误判场景：代码块内的 `#` 不是标题；引用和列表内的标题嵌套层级大于 0，天然被过滤；列表项内缩进的围栏和未闭合的围栏都有正确的行范围。
- 标题边界和代码块行号来自同一次解析，不需要为了清洗再解析一遍。

**注意事项：**

- 不使用 `gfm-like` 预设。它默认开启 linkify，在缺少 `linkify-it-py` 的环境中初始化会直接抛出 `ModuleNotFoundError`。
- front matter 需要单独防护：CommonMark 不认识 front matter，`---` / `title: x` / `---` 会被解析成标题为 `title: x` 的二级标题。处理方式是文件首行为 `---` 且后续存在 `---` 或 `...` 闭合行时，该范围内的标题不参与切分，front matter 原样留在前言节中。

**备选方案：**

- 手写正则跟踪围栏和标题：需要自行处理围栏字符、长度、缩进、嵌套，已知在多种情况下会误判。

### 4. Markdown 清洗保留语法，只规范代码块之外的空白

**决定：** 在 `text_cleaner.py` 新增 `clean_markdown_text(lines, start, end, code_lines) -> str`，按节清洗：非代码行去除行尾空白，连续空行压缩为一个空行，去除节首尾的空白行；代码行原样保留。不调用 `clean_text()`。

**原因：**

- `clean_text()` 的空白合并规则会改变列表缩进和代码内容，不适用于 Markdown。
- 保留 Markdown 语法后，标题、列表和表格的结构对后续按标题分块和大模型阅读都直接可用。
- 代码块不会跨节：节的边界是顶层标题行，而标题不可能出现在代码块内，所以按节清洗与按全文清洗结果一致。

**备选方案：**

- 把 Markdown 去标记转换为纯文本：原型验证中标题层级、列表符号和表格结构都会丢失，front matter 还会残留一行 `title:`；需要额外维护一套渲染逻辑，后续分块也得回头解析原文。

### 5. 读取与异常处理对齐 PDF 的规则

**决定：**

- 使用 `Path.read_text(encoding="utf-8-sig")` 读取，带 BOM 和不带 BOM 的 UTF-8 文件都能正确读取，BOM 不进入文本。
- 读取后把换行符统一为 `\n` 再解析，节的 `text` 保存统一换行符后的原文。
- 文件不存在时抛出 `FileNotFoundError`；路径不是文件、读取失败、无法按 UTF-8 解码、没有可提取的文本时抛出 `MarkdownDocumentError`（定义在 `markdown_parser.py`）。
- `UnicodeDecodeError` 不是 `OSError` 的子类，需要单独捕获并转换为 `MarkdownDocumentError`。
- 不做非 UTF-8 编码的回退解码：解码失败时明确报错，避免静默误解码。

### 6. 统一入口按扩展名分发

**决定：** 在 `pipeline.py` 新增 `process_document(file_path, output_dir="output")`，用小写后的扩展名查表选择解析器：`.pdf` 对应 `extract_pdf_content`，`.md` 和 `.markdown` 对应 `extract_markdown_content`。扩展名不在表中时抛出 `UnsupportedFileTypeError`（定义在 `pipeline.py`），此时不创建输出目录。`process_pdf()` 保留不动。

**备选方案：**

- 再新增一个 `process_markdown()`：与 `process_pdf()` 只差一行解析调用，统一入口已经覆盖这个用途。

### 7. 导出格式只做增量调整

**决定：**

- JSON：顶层增加 `source_type`，每一段增加 `heading_path` 和 `heading_level`。字段名 `total_pages`、`page_number` 对 Markdown 分别表示节总数和节序号。
- TXT 分隔标记：PDF 保持 `========== 第 N 页 ==========` 不变；Markdown 使用 `========== 第 N 节  <标题路径> ==========`，前言节的标题路径显示为“无标题”。
- 输出文件的命名规则不变：`notes.md` 导出为 `notes.json` 和 `notes.txt`。

### 8. 测试沿用现有做法

**决定：** Markdown 测试文件在测试中写入 `tmp_path`，不提交真实文档。新增 `tests/test_markdown_parser.py`，并在 `test_text_cleaner.py`、`test_exporters.py`、`test_pipeline.py` 中补充用例。

重点覆盖：

- 读取与异常：不存在、路径是目录、非 UTF-8 字节、空文件、纯空白文件、带 BOM 和 CRLF 的文件。
- 标题切分：多级标题的顺序与标题路径、各节原文拼接等于全文、前言节、无标题文档、层级跳跃、只有标题行的节、代码块内的 `#`、引用和列表内的标题、front matter、未闭合的围栏。
- 清洗：代码之外的空白被规范，代码块内的缩进、连续空格和空行保持不变。
- 导出与入口：Markdown 的 JSON 字段和 TXT 标记，PDF 的 JSON 标明来源类型且 TXT 标记不变，统一入口对 `.md`、大写扩展名 `.MD`、`.markdown`、`.pdf` 的分发，不支持的类型和解析失败时不产生输出。

## Risks / Trade-offs

- [`page_number` 和 `total_pages` 对 Markdown 是借用的字段名] → 在模块 README 中说明其对两种格式各自的含义；待分块阶段确定锚点语义后，再统一改名为中性的片段字段。
- [只含 front matter 的文件会被当作一个有效的前言节] → 本阶段不解析 front matter，该情况留给元数据注入阶段处理。
- [用加粗代替标题的文档无法识别出节] → 保持原文，不做猜测，由分块阶段的长度规则兜底。
- [`html_block` 整块不参与清洗] → 取舍是少清洗优于误破坏，代价是原始 HTML 块中可能残留行尾空白。
- [`markdown-it-py` 是纯 Python 实现] → 原型实测 0.5 KB 文件约 1 毫秒，2.5 MB 的合成文档约 6 秒；KB 级笔记无感知，MB 级文档为秒级，当前阶段可接受。
- [新增直接依赖] → 显式写入 `backend/requirements.txt`，与现有依赖一样不锁定版本；CommonMark 语义稳定。
- [PDF 的 JSON 输出增加字段] → 属于增量变更，现有测试只断言具体字段，不受影响。

## Migration Plan

不涉及数据迁移和线上服务切换。

实施顺序：

1. 在 `backend/requirements.txt` 中加入 `markdown-it-py`。
2. 扩展 `models.py` 的数据结构。
3. 在 `text_cleaner.py` 中实现 Markdown 清洗。
4. 新增 `markdown_parser.py`，实现读取、切分和解析。
5. 调整 `exporters.py` 的 JSON 字段和 TXT 标记。
6. 在 `pipeline.py` 中新增统一入口。
7. 补充测试并执行全量测试，确认 PDF 用例无回归。
8. 更新模块 README、项目 README 和主规范。

回滚策略：

- 新增代码集中在 `markdown_parser.py` 和各文件的增量部分，回滚时移除这些内容以及 `markdown-it-py` 依赖即可，PDF 链路不受影响。
- 测试生成的 Markdown 文件和解析输出不作为源代码提交。
