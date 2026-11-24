from pathlib import Path

import pymupdf

from backend.app.document_parser.models import (
    DocumentContent,
    PageContent,
)


class PDFDocumentError(Exception):
    """PDF 文档读取或校验失败。"""


def open_pdf_document(pdf_path: str | Path) -> pymupdf.Document:
    """
    打开并校验 PDF 文件。

    Args:
        pdf_path: PDF 文件路径。

    Returns:
        已打开的 PyMuPDF Document 对象。
        调用方负责在使用完毕后关闭文档。

    Raises:
        FileNotFoundError: 文件不存在。
        PDFDocumentError: 路径不是普通文件，或文件不是有效 PDF。
    """
    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF 文件不存在：{path}")

    if not path.is_file():
        raise PDFDocumentError(f"指定路径不是文件：{path}")

    try:
        document = pymupdf.open(path)

        if not document.is_pdf:
            document.close()
            raise PDFDocumentError(f"文件不是有效的 PDF：{path}")

        return document

    except PDFDocumentError:
        raise
    except Exception as exc:
        raise PDFDocumentError(f"无法读取 PDF 文件：{path}，原因：{exc}") from exc


def extract_pdf_content(
    pdf_path: str | Path,
) -> DocumentContent:
    """
    提取 PDF 全部页面的原始文本。

    页码从 1 开始，并保留原始页面顺序。
    """
    path = Path(pdf_path)
    document = open_pdf_document(path)

    try:
        pages = []

        for page_index in range(document.page_count):
            page = document.load_page(page_index)
            text = page.get_text("text")

            pages.append(
                PageContent(
                    page_number=page_index + 1,
                    text=text,
                )
            )

        return DocumentContent(
            filename=path.name,
            total_pages=document.page_count,
            pages=pages,
        )
    finally:
        document.close()
