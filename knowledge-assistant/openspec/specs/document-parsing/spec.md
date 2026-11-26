# document-parsing Specification

## Purpose

定义个人知识库 AI 助手的基础文档解析能力，将 PDF 和 Markdown 文档转换为保留结构锚点（PDF 页码、Markdown 标题路径）和基本结构的文本数据，为后续文本分块、向量化和知识检索提供统一输入。

## Requirements

### Requirement: PDF 文件读取

系统 MUST 支持读取有效的 PDF 文件，并在文件无法读取或格式无效时返回明确的错误信息。

#### Scenario: 成功读取 PDF 文件
- **WHEN** 用户提供一个有效且可读取的 PDF 文件
- **THEN** 系统 SHALL 成功读取该文件并进入文本提取流程

#### Scenario: 文件不存在
- **WHEN** 用户提供的 PDF 文件路径不存在
- **THEN** 系统 SHALL 返回明确的文件不存在错误信息

#### Scenario: 文件不是有效 PDF
- **WHEN** 用户提供的文件不是有效的 PDF 文档
- **THEN** 系统 SHALL 返回明确的文件格式或解析错误信息

### Requirement: PDF 逐页文本提取

系统 MUST 按照 PDF 原始页序提取每一页的文本内容，并保留对应页码。

#### Scenario: 成功提取多页 PDF
- **WHEN** 用户提供一个包含多页文本的有效 PDF
- **THEN** 系统 SHALL 按照原始页序逐页提取文本
- **AND** 每页提取结果 SHALL 包含对应的页码和文本内容

#### Scenario: PDF 包含空白页
- **WHEN** 用户提供的 PDF 中存在没有可提取文本的页面
- **THEN** 系统 SHALL 保留该页面对应的页码记录
- **AND** 该页面的文本内容 SHALL 为空字符串

### Requirement: 文本清洗

系统 MUST 对提取的文本进行基础清洗，同时尽可能保留原始段落和列表结构。

#### Scenario: 清理多余空白字符
- **WHEN** 提取的文本包含连续空格、多余空行或首尾空白
- **THEN** 系统 SHALL 清理不必要的空白字符
- **AND** SHALL 保留合理的段落分隔

#### Scenario: 保留基本文本结构
- **WHEN** 提取的文本包含多个段落或列表内容
- **THEN** 系统 SHALL 尽可能保留原有的段落和列表换行结构

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

### Requirement: PDF 解析异常处理

系统 MUST 对 PDF 解析过程中的异常情况进行合理处理，不得因单个异常页面导致整个程序无明确反馈地终止。

#### Scenario: 单页提取发生异常
- **WHEN** PDF 解析过程中某一页发生无法正常提取文本的异常
- **THEN** 系统 SHALL 提供明确的异常信息
- **AND** SHALL 保留能够成功处理的页面结果，或明确报告本次解析失败

#### Scenario: PDF 不包含可提取文本
- **WHEN** PDF 所有页面均没有可提取的文本内容
- **THEN** 系统 SHALL 明确报告文档没有可提取的文本内容
- **AND** SHALL 不得将其误报为成功提取了有效文本

### Requirement: Markdown 文件读取

系统 MUST 支持读取有效的 Markdown 文件，并在文件无法读取或格式无效时返回明确的错误信息。

#### Scenario: 成功读取 Markdown 文件
- **WHEN** 用户提供一个有效且可读取的 Markdown 文件
- **THEN** 系统 SHALL 成功读取该文件并进入解析流程

#### Scenario: 文件不存在
- **WHEN** 用户提供的 Markdown 文件路径不存在
- **THEN** 系统 SHALL 返回明确的文件不存在错误信息

#### Scenario: 文件不是有效 UTF-8 文本
- **WHEN** 用户提供的文件不是有效的 UTF-8 文本
- **THEN** 系统 SHALL 返回明确的解码或格式错误信息

### Requirement: Markdown 标题切分

系统 MUST 按 Markdown 标题结构将文档切分为多个节，并保留每节的标题路径和标题层级，使后续分块可以引用所在章节。

#### Scenario: 按标题切分文档
- **WHEN** 用户提供一个包含多个标题的有效 Markdown 文档
- **THEN** 系统 SHALL 按标题将文档切分为多个节
- **AND** 每个节 SHALL 包含该节正文和其标题路径

#### Scenario: 标题路径反映层级
- **WHEN** Markdown 文档包含多级嵌套标题
- **THEN** 每个节的标题路径 SHALL 从顶层标题逐级串联到该节标题
- **AND** 每个节 SHALL 记录标题层级

#### Scenario: 标题前的正文归入前言节
- **WHEN** 文档在第一个标题之前包含正文
- **THEN** 该部分正文 SHALL 归入一个标题路径为空的前言节

### Requirement: Markdown 文本清洗

系统 MUST 对 Markdown 解析出的各节文本进行基础清洗，同时保留 Markdown 语义语法和代码块内容。

#### Scenario: 清理多余空白
- **WHEN** 节文本包含连续空格或多余空行
- **THEN** 系统 SHALL 清理多余空白并保留段落结构

#### Scenario: 保留 Markdown 语法
- **WHEN** 节文本包含列表、链接、粗体等 Markdown 语法
- **THEN** 系统 SHALL 保留这些语法标记，不将其转换为纯文本

#### Scenario: 代码块内容逐字保留
- **WHEN** 节文本包含围栏代码块
- **THEN** 系统 SHALL 逐字保留代码块内容，不做空白归一化

### Requirement: 按文件类型选择解析器

系统 MUST 根据文件扩展名选择对应的解析器：PDF 文件走 PDF 解析流程，Markdown 文件（.md/.markdown）走 Markdown 解析流程，其他类型返回明确的错误信息。

#### Scenario: 选择 PDF 解析器
- **WHEN** 用户传入 .pdf 文件
- **THEN** 系统 SHALL 使用 PDF 解析流程

#### Scenario: 选择 Markdown 解析器
- **WHEN** 用户传入 .md 或 .markdown 文件
- **THEN** 系统 SHALL 使用 Markdown 解析流程

#### Scenario: 不支持的文件类型
- **WHEN** 用户传入其他扩展名的文件
- **THEN** 系统 SHALL 返回明确的不支持文件类型错误信息
