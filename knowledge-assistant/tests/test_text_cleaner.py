from backend.app.document_parser.text_cleaner import clean_markdown_text, clean_text


def _clean_markdown(text, code_lines=()):
    lines = text.split("\n")
    return clean_markdown_text(lines, 0, len(lines), set(code_lines))


def test_clean_text_removes_leading_and_trailing_whitespace():
    result = clean_text("   Hello World   ")

    assert result.cleaned_text == "Hello World"


def test_clean_text_merges_consecutive_spaces():
    result = clean_text("Hello    World\t\tPython")

    assert result.cleaned_text == "Hello World Python"


def test_clean_text_compresses_multiple_blank_lines():
    result = clean_text("第一段\n\n\n\n第二段")

    assert result.cleaned_text == "第一段\n\n第二段"


def test_clean_text_preserves_original_text():
    original = "  Hello    World  "

    result = clean_text(original)

    assert result.original_text == original
    assert result.cleaned_text == "Hello World"


def test_clean_text_preserves_paragraphs():
    original = "第一段内容\n\n第二段内容"

    result = clean_text(original)

    assert result.cleaned_text == original


def test_clean_text_preserves_numbered_list_lines():
    original = "处理流程：\n" "1. 检查数据源\n" "2. 检查数据格式\n" "3. 重新执行任务"

    result = clean_text(original)

    assert result.cleaned_text == original


def test_clean_text_preserves_bullet_list_lines():
    original = "注意事项：\n" "- 不要重复提交\n" "- 保留原始日志"

    result = clean_text(original)

    assert result.cleaned_text == original


def test_clean_text_preserves_paragraph_and_list_structure():
    original = (
        "问题描述：\n"
        "数据导入失败。\n\n"
        "处理步骤：\n"
        "1. 检查数据源\n"
        "2. 检查数据格式\n\n"
        "处理结果：\n"
        "数据导入成功。"
    )

    result = clean_text(original)

    assert result.cleaned_text == original


def test_clean_markdown_text_strips_trailing_whitespace():
    assert _clean_markdown("# 标题   \n\n正文   ") == "# 标题\n\n正文"


def test_clean_markdown_text_compresses_blank_lines():
    assert _clean_markdown("第一段\n\n\n\n第二段") == "第一段\n\n第二段"


def test_clean_markdown_text_preserves_code_lines_verbatim():
    text = '```python\nx = "a    b"\n\n\n    return x\n```'

    assert _clean_markdown(text, code_lines=range(0, 5)) == text


def test_clean_markdown_text_keeps_code_trailing_whitespace():
    text = "```python\nx = 1   \n```"
    code_lines = {0, 1, 2}

    assert _clean_markdown(text, code_lines) == text


def test_clean_markdown_text_cleans_text_around_code():
    text = "正文   \n\n```python\nx = 1\n\n\n```\n\n\n结尾  "
    code_lines = {2, 3, 4, 5, 6}

    assert _clean_markdown(text, code_lines) == "正文\n\n```python\nx = 1\n\n\n```\n\n结尾"


def test_clean_markdown_text_keeps_list_indentation_and_table_rows():
    text = "- 一级列表\n    - 二级列表\n\n| 列A | 列B |\n|---|---|\n| 1 | 2 |"

    assert _clean_markdown(text) == text


def test_clean_markdown_text_keeps_leading_indentation_of_plain_lines():
    assert _clean_markdown("    缩进内容\n    第二行") == "    缩进内容\n    第二行"


def test_clean_markdown_text_supports_section_range():
    lines = "# 标题\n\n正文   ".split("\n")

    assert clean_markdown_text(lines, 2, 3, set()) == "正文"


def test_clean_markdown_text_drops_blank_section():
    assert _clean_markdown("\n\n\n") == ""
