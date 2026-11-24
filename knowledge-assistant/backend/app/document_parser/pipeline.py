from pathlib import Path

from backend.app.document_parser.exporters import export_document
from backend.app.document_parser.models import DocumentContent
from backend.app.document_parser.pdf_parser import extract_pdf_content


def process_pdf(
    pdf_path: str | Path,
    output_dir: str | Path = "output",
) -> tuple[DocumentContent, dict[str, Path]]:
    """
    完成 PDF 解析、逐页文本清洗和 TXT/JSON 导出。

    Args:
        pdf_path: 输入 PDF 文件路径。
        output_dir: 导出目录，默认为项目根目录下的 output。

    Returns:
        (document, output_files)
        document 为完整的逐页解析结果；
        output_files 包含 json、txt 两种格式的导出路径。

    Raises:
        FileNotFoundError: 输入文件不存在。
        PDFDocumentError: PDF 无效、无法读取或没有可提取文本。
        ExportError: 输出目录创建或文件导出失败。
    """
    document = extract_pdf_content(pdf_path)
    output_files = export_document(document, output_dir)
    return document, output_files

