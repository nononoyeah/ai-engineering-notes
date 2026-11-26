import pytest

from backend.app.document_parser.markdown_parser import (
    MarkdownDocumentError,
    extract_markdown_content,
)


def write_markdown(directory, filename, content, encoding="utf-8"):
    """写入 Markdown 测试文件，返回文件路径。"""
    path = directory / filename
    path.write_bytes(content.encode(encoding))
    return path


def test_extract_markdown_content_reads_valid_file(tmp_path):
    md_path = write_markdown(tmp_path, "notes.md", "# 标题\n\n正文")

    result = extract_markdown_content(md_path)

    assert result.filename == "notes.md"
    assert result.source_type == "markdown"
    assert result.total_pages == 1
    assert result.pages[0].page_number == 1
    assert result.pages[0].text == "# 标题\n\n正文"


def test_extract_markdown_content_reports_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="Markdown 文件不存在"):
        extract_markdown_content(tmp_path / "missing.md")


def test_extract_markdown_content_rejects_directory(tmp_path):
    with pytest.raises(MarkdownDocumentError, match="指定路径不是文件"):
        extract_markdown_content(tmp_path)


def test_extract_markdown_content_rejects_non_utf8_file(tmp_path):
    md_path = write_markdown(tmp_path, "gbk.md", "# 中文标题", encoding="gbk")

    with pytest.raises(MarkdownDocumentError, match="无法读取 Markdown 文件"):
        extract_markdown_content(md_path)


def test_extract_markdown_content_rejects_empty_file(tmp_path):
    md_path = write_markdown(tmp_path, "empty.md", "")

    with pytest.raises(MarkdownDocumentError, match="没有可提取的文本内容"):
        extract_markdown_content(md_path)


def test_extract_markdown_content_rejects_whitespace_only_file(tmp_path):
    md_path = write_markdown(tmp_path, "blank.md", " \n\n\n")

    with pytest.raises(MarkdownDocumentError, match="没有可提取的文本内容"):
        extract_markdown_content(md_path)


def test_extract_markdown_content_handles_bom_and_crlf(tmp_path):
    md_path = write_markdown(tmp_path, "bom.md", "\ufeff# 标题\r\n\r\n正文   \r\n")

    result = extract_markdown_content(md_path)

    assert "\ufeff" not in result.pages[0].text
    assert result.pages[0].text == "# 标题\n\n正文   \n"
    assert result.pages[0].cleaned_text == "# 标题\n\n正文"


def test_extract_markdown_content_splits_by_heading_levels(tmp_path):
    content = (
        "# 一级标题\n\n前言内容\n\n"
        "## 二级标题\n\n二级正文\n\n"
        "### 三级标题\n\n三级正文\n\n"
        "## 另一个二级\n\n另一正文\n"
    )
    md_path = write_markdown(tmp_path, "levels.md", content)

    result = extract_markdown_content(md_path)

    assert [page.heading_level for page in result.pages] == [1, 2, 3, 2]
    assert result.pages[0].heading_path == "一级标题"
    assert result.pages[1].heading_path == "一级标题 > 二级标题"
    assert result.pages[2].heading_path == "一级标题 > 二级标题 > 三级标题"
    assert result.pages[3].heading_path == "一级标题 > 另一个二级"
    assert [page.page_number for page in result.pages] == [1, 2, 3, 4]
    assert result.total_pages == 4
    assert "二级正文" in result.pages[1].text


def test_extract_markdown_content_sections_reassemble_full_text(tmp_path):
    content = (
        "# 一级\n\n正文\n\n```python\n# 注释\n```\n\n"
        "## 二级\n\n> # 引用\n\n- # 列表\n\n#### 跳级\n\n结尾\n"
    )
    md_path = write_markdown(tmp_path, "lossless.md", content)

    result = extract_markdown_content(md_path)

    assert "".join(page.text for page in result.pages) == content


def test_extract_markdown_content_preamble_before_first_heading(tmp_path):
    content = "前言内容\n\n# 标题\n\n正文\n"
    md_path = write_markdown(tmp_path, "preamble.md", content)

    result = extract_markdown_content(md_path)

    assert result.total_pages == 2
    assert result.pages[0].heading_level == 0
    assert result.pages[0].heading_path == ""
    assert result.pages[0].text == "前言内容\n\n"
    assert result.pages[1].heading_path == "标题"


def test_extract_markdown_content_skips_blank_preamble(tmp_path):
    md_path = write_markdown(tmp_path, "blank_preamble.md", "\n\n# 标题\n\n正文\n")

    result = extract_markdown_content(md_path)

    assert result.total_pages == 1
    assert result.pages[0].page_number == 1
    assert result.pages[0].heading_path == "标题"


def test_extract_markdown_content_no_headings_single_section(tmp_path):
    md_path = write_markdown(tmp_path, "plain.md", "第一段\n\n第二段\n")

    result = extract_markdown_content(md_path)

    assert result.total_pages == 1
    assert result.pages[0].heading_level == 0
    assert result.pages[0].text == "第一段\n\n第二段\n"


def test_extract_markdown_content_heading_level_jump(tmp_path):
    md_path = write_markdown(tmp_path, "jump.md", "# 一级\n\n#### 四级\n\n正文\n")

    result = extract_markdown_content(md_path)

    assert result.pages[1].heading_level == 4
    assert result.pages[1].heading_path == "一级 > 四级"


def test_extract_markdown_content_heading_only_section(tmp_path):
    md_path = write_markdown(tmp_path, "parent.md", "## 父标题\n\n### 子标题\n\n子正文\n")

    result = extract_markdown_content(md_path)

    assert result.total_pages == 2
    assert result.pages[0].text == "## 父标题\n\n"
    assert result.pages[0].heading_path == "父标题"
    assert result.pages[1].heading_path == "父标题 > 子标题"


def test_extract_markdown_content_ignores_hash_inside_code_block(tmp_path):
    content = "# 标题\n\n```python\n# 代码里的注释\n## 也不是标题\n```\n"
    md_path = write_markdown(tmp_path, "code.md", content)

    result = extract_markdown_content(md_path)

    assert result.total_pages == 1
    assert "# 代码里的注释" in result.pages[0].text
    assert "## 也不是标题" in result.pages[0].text


def test_extract_markdown_content_ignores_headings_in_quote_and_list(tmp_path):
    content = "# 标题\n\n> # 引用里的标题\n\n- # 列表里的标题\n"
    md_path = write_markdown(tmp_path, "quote.md", content)

    result = extract_markdown_content(md_path)

    assert result.total_pages == 1
    assert "> # 引用里的标题" in result.pages[0].text
    assert "- # 列表里的标题" in result.pages[0].text


def test_extract_markdown_content_front_matter_not_heading(tmp_path):
    content = "---\ntitle: 测试\ntags: [a, b]\n---\n# 标题\n\n正文\n"
    md_path = write_markdown(tmp_path, "front.md", content)

    result = extract_markdown_content(md_path)

    assert result.total_pages == 2
    assert result.pages[0].heading_level == 0
    assert result.pages[0].text == "---\ntitle: 测试\ntags: [a, b]\n---\n"
    assert result.pages[1].heading_path == "标题"
    for page in result.pages:
        assert page.heading_path != "title: 测试"


def test_extract_markdown_content_unclosed_fence(tmp_path):
    content = '# 标题\n\n```python\nx = "a    b"\n\nprint(x)\n'
    md_path = write_markdown(tmp_path, "unclosed.md", content)

    result = extract_markdown_content(md_path)

    assert result.total_pages == 1
    assert 'x = "a    b"' in result.pages[0].text


def test_extract_markdown_content_setext_heading(tmp_path):
    md_path = write_markdown(tmp_path, "setext.md", "标题\n===\n\n正文\n")

    result = extract_markdown_content(md_path)

    assert result.total_pages == 1
    assert result.pages[0].heading_level == 1
    assert result.pages[0].heading_path == "标题"
    assert "正文" in result.pages[0].text


def test_extract_markdown_content_strips_inline_markup_from_titles(tmp_path):
    md_path = write_markdown(tmp_path, "markup.md", "## **加粗** 和 `代码`\n\n正文\n")

    result = extract_markdown_content(md_path)

    assert result.pages[0].heading_path == "加粗 和 代码"


def test_extract_markdown_content_preserves_code_verbatim_in_cleaned_text(tmp_path):
    code = '```python\n# 注释\nx = "a    b"\n\n\n    return x\n```'
    md_path = write_markdown(tmp_path, "codeclean.md", f"# 标题\n\n{code}\n")

    result = extract_markdown_content(md_path)

    assert code in result.pages[0].cleaned_text


def test_extract_markdown_content_cleans_text_outside_code(tmp_path):
    md_path = write_markdown(tmp_path, "textclean.md", "正文   \n\n\n\n结尾   \n")

    result = extract_markdown_content(md_path)

    assert result.pages[0].text == "正文   \n\n\n\n结尾   \n"
    assert result.pages[0].cleaned_text == "正文\n\n结尾"


def test_extract_markdown_content_cleans_each_section_independently(tmp_path):
    md_path = write_markdown(
        tmp_path,
        "sections.md",
        "# 一级\n\n正文一\n\n\n\n## 二级\n\n正文二\n",
    )

    result = extract_markdown_content(md_path)

    assert result.pages[0].cleaned_text == "# 一级\n\n正文一"
    assert result.pages[1].cleaned_text == "## 二级\n\n正文二"
