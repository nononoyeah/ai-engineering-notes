from backend.app.document_parser.text_cleaner import clean_text


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
