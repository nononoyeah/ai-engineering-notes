# Spec Delta

## ADDED Requirements

### Requirement: Markdown 文件读取

系统 MUST 支持读取 Markdown 文件（扩展名为 `.md` 或 `.markdown`，不区分大小写），并在文件路径不存在、路径不是文件、内容无法按 UTF-8 解码或没有可提取文本时返回明确的错误信息。

#### Scenario: 成功读取 Markdown 文件
- **WHEN** 用户提供一个有效的 Markdown 文件
- **THEN** 系统 SHALL 成功读取该文件并进入标题切分流程

#### Scenario: Markdown 文件不存在
- **WHEN** 用户提供的 Markdown 文件路径不存在
- **THEN** 系统 SHALL 返回明确的文件不存在错误信息

#### Scenario: 路径不是文件
- **WHEN** 用户提供的 Markdown 路径是一个目录
- **THEN** 系统 SHALL 返回明确的路径不是文件错误信息

#### Scenario: 文件内容不是 UTF-8 编码
- **WHEN** Markdown 文件的内容无法按 UTF-8 解码
- **THEN** 系统 SHALL 返回明确的读取失败错误信息，并说明原因

#### Scenario: Markdown 文件没有可提取的文本
- **WHEN** Markdown 文件为空或只包含空白字符
- **THEN** 系统 SHALL 明确报告文档没有可提取的文本内容
- **AND** SHALL 不得将其误报为成功解析

#### Scenario: 文件包含 BOM 或 Windows 换行符
- **WHEN** Markdown 文件以 UTF-8 BOM 开头，或使用 Windows 换行符
- **THEN** 系统 SHALL 正常读取该文件
- **AND** 解析结果中的文本 SHALL 不包含 BOM，且换行符统一为 `\n`

### Requirement: Markdown 标题切分

系统 MUST 按 Markdown 顶层标题（一级至六级）将文档切分为按原文顺序排列的节，每一节从其标题行开始，到下一个任意层级的标题之前结束，并记录标题路径和标题层级；除首个标题之前的纯空白外，各节 SHALL 覆盖全文且互不重叠。

#### Scenario: 按多级标题切分文档
- **WHEN** Markdown 文档包含一级、二级和三级标题及对应的正文
- **THEN** 系统 SHALL 按原文顺序为每个标题生成一个节
- **AND** 每个节的标题路径 SHALL 由其上级标题依次连接组成
- **AND** 每个节的标题层级 SHALL 与标题的级数一致

#### Scenario: 第一个标题之前存在内容
- **WHEN** Markdown 文档在第一个标题之前存在正文
- **THEN** 系统 SHALL 将这部分内容作为第一个节
- **AND** 该节的标题路径 SHALL 为空字符串，标题层级 SHALL 为 0

#### Scenario: 各节原文构成完整文档
- **WHEN** Markdown 文档已完成标题切分
- **THEN** 按顺序拼接各节的原始文本 SHALL 得到换行符统一后的完整文档内容

#### Scenario: 文档没有标题
- **WHEN** Markdown 文档不包含任何标题
- **THEN** 系统 SHALL 将整篇文档作为唯一的一个节
- **AND** 该节的标题层级 SHALL 为 0

#### Scenario: 标题层级跳跃
- **WHEN** 文档中某个标题与上一个标题之间跳过了中间层级
- **THEN** 该节的标题路径 SHALL 由实际存在的上级标题依次连接组成

#### Scenario: 标题下只有子标题
- **WHEN** 某个标题之后直接紧跟下一级标题，没有其他正文
- **THEN** 系统 SHALL 仍然为该标题生成一个只包含标题行的节

#### Scenario: 代码块中的井号行不被识别为标题
- **WHEN** 代码块内存在以 `#` 开头的行
- **THEN** 系统 SHALL 不将其识别为标题
- **AND** 该代码块 SHALL 完整保留在其所属的节中

#### Scenario: 引用和列表中的标题不作为切分边界
- **WHEN** 标题位于引用块或列表项内
- **THEN** 系统 SHALL 不以该标题作为节的边界
- **AND** 该内容 SHALL 保留在其所属的节中

#### Scenario: 文档开头的 front matter 不被识别为标题
- **WHEN** Markdown 文档以 YAML front matter（`---` 包围的元数据块）开头
- **THEN** 系统 SHALL 不将 front matter 的内容识别为标题
- **AND** front matter SHALL 原样保留在第一个标题之前的节中

### Requirement: Markdown 文本清洗

系统 MUST 对每个 Markdown 节进行基础清洗：统一换行符，去除首尾空白和行尾空白，并将连续空行压缩为一个空行；清洗 SHALL 保留 Markdown 语法，代码块内的内容 MUST 原样保留。

#### Scenario: 清理代码块之外的空白噪声
- **WHEN** Markdown 节的正文中存在行尾空白、连续多个空行或首尾空白行
- **THEN** 系统 SHALL 清理这些空白
- **AND** SHALL 保留合理的段落分隔

#### Scenario: 代码块内容原样保留
- **WHEN** Markdown 节的代码块内存在缩进、连续空格或连续空行
- **THEN** 清洗后的代码块内容 SHALL 与原文完全一致

#### Scenario: 保留 Markdown 结构
- **WHEN** Markdown 节包含标题、嵌套列表或表格
- **THEN** 清洗后的文本 SHALL 保留标题标记、列表缩进和表格行

#### Scenario: 原始文本与清洗文本分别保存
- **WHEN** Markdown 节完成清洗
- **THEN** 节的原始文本 SHALL 保持不变
- **AND** 清洗结果 SHALL 单独保存

### Requirement: 按文件类型选择解析器

系统 MUST 根据文件扩展名（不区分大小写）为文档选择对应的解析器：`.pdf` 使用 PDF 解析，`.md` 和 `.markdown` 使用 Markdown 解析；解析完成后 SHALL 使用相同的方式导出 TXT 和 JSON 文件。

#### Scenario: 通过统一入口处理 Markdown 文件
- **WHEN** 用户通过统一入口提供一个有效的 Markdown 文件
- **THEN** 系统 SHALL 完成 Markdown 解析和清洗
- **AND** SHALL 生成对应的 TXT 和 JSON 文件

#### Scenario: 通过统一入口处理 PDF 文件
- **WHEN** 用户通过统一入口提供一个有效的 PDF 文件
- **THEN** 系统 SHALL 得到与直接调用 PDF 处理入口一致的结果

#### Scenario: 文件类型不受支持
- **WHEN** 用户通过统一入口提供的文件扩展名不是 `.pdf`、`.md` 或 `.markdown`
- **THEN** 系统 SHALL 返回明确的不支持的文件类型错误信息
- **AND** SHALL 不生成任何输出文件和输出目录

#### Scenario: 解析失败时不导出
- **WHEN** 通过统一入口处理的文档在解析阶段失败
- **THEN** 系统 SHALL 返回解析阶段的错误信息
- **AND** SHALL 不生成任何输出文件和输出目录

## MODIFIED Requirements

### Requirement: TXT 文件输出

系统 MUST 支持将 PDF 或 Markdown 的解析结果输出为 TXT 文件，并保留各段文本的顺序；PDF 的段为页，Markdown 的段为节。

#### Scenario: 成功生成 TXT 文件
- **WHEN** 有效 PDF 已完成文本提取和清洗
- **THEN** 系统 SHALL 生成对应的 TXT 文件
- **AND** 输出内容 SHALL 按照原始页序组织

#### Scenario: Markdown 解析结果生成 TXT 文件
- **WHEN** 有效 Markdown 文档已完成标题切分和清洗
- **THEN** 系统 SHALL 生成对应的 TXT 文件
- **AND** 输出内容 SHALL 按节的原始顺序组织
- **AND** 每个节 SHALL 带有包含节序号和标题路径的分隔标记

#### Scenario: PDF 的 TXT 分隔标记保持不变
- **WHEN** 导出 PDF 解析结果
- **THEN** 每页的分隔标记 SHALL 仍为原有的页码标记

### Requirement: JSON 文件输出

系统 MUST 支持将 PDF 或 Markdown 的解析结果输出为结构化 JSON 文件，并保留文件名、来源类型、总段数和逐段文本信息；Markdown 的每一段 SHALL 额外包含标题路径和标题层级。

#### Scenario: 成功生成 JSON 文件
- **WHEN** 有效 PDF 已完成文本提取和清洗
- **THEN** 系统 SHALL 生成对应的 JSON 文件
- **AND** JSON SHALL 包含文件名、总页数和逐页解析结果
- **AND** 每页解析结果 SHALL 包含页码和文本内容

#### Scenario: JSON 文件包含中文内容
- **WHEN** PDF 中包含可正常提取的中文文本
- **THEN** 系统 SHALL 在 JSON 输出中正确保留中文内容

#### Scenario: Markdown 解析结果生成 JSON 文件
- **WHEN** 有效 Markdown 文档已完成标题切分和清洗
- **THEN** 系统 SHALL 生成对应的 JSON 文件
- **AND** JSON SHALL 标明来源类型为 Markdown
- **AND** 每个节的解析结果 SHALL 包含节序号、标题路径、标题层级、原始文本和清洗后文本

#### Scenario: PDF 解析结果标明来源类型
- **WHEN** 导出 PDF 解析结果
- **THEN** JSON SHALL 标明来源类型为 PDF
- **AND** 原有的文件名、总页数和逐页解析结果字段 SHALL 保持不变
