"""Optional Docling adapter for model-free PDF and Office conversions."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from .core import SourceDocument

MAX_BYTES = 10 * 1024 * 1024
TEXT_SUFFIXES = {".txt", ".md"}
DOCLING_SUFFIXES = {".pdf", ".docx", ".pptx"}
SUPPORTED_SUFFIXES = TEXT_SUFFIXES | DOCLING_SUFFIXES

CONVERTED_MARKDOWN = "converted_markdown_line"


class DocumentReadError(ValueError):
    """Unsupported, unreadable, incomplete, or oversized input document."""


def _docling_extract(path: Path) -> str:
    try:
        from docling.datamodel.base_models import ConversionStatus, InputFormat
        from docling.datamodel.pipeline_options import NativePdfPipelineOptions
        from docling.document_converter import (
            DocumentConverter,
            NativePdfFormatOption,
        )
    except ImportError as exc:
        raise DocumentReadError(
            "Instale a integração para PDF/Office: pip install 'docdiff-ai[documents]'"
        ) from exc

    # The native PDF pipeline requires no downloaded ML models. Scanned-only
    # PDFs are intentionally unsupported until a separate evaluated OCR path exists.
    try:
        options = {}
        if path.suffix.lower() == ".pdf":
            options[InputFormat.PDF] = NativePdfFormatOption(
                pipeline_options=NativePdfPipelineOptions(
                    generate_page_images=False,
                    generate_picture_images=False,
                )
            )
            allowed = [InputFormat.PDF]
        elif path.suffix.lower() == ".docx":
            allowed = [InputFormat.DOCX]
        else:
            allowed = [InputFormat.PPTX]
        converter = DocumentConverter(allowed_formats=allowed, format_options=options)
        result = converter.convert(str(path), raises_on_error=False)
        if result.status != ConversionStatus.SUCCESS:
            raise DocumentReadError(
                f"Conversão não concluída ({result.status}): {path.name}. "
                "Confira se o documento está corrompido ou protegido."
            )
        text = result.document.export_to_markdown()
    except DocumentReadError:
        raise
    except Exception as exc:
        # Conversion is an optional external dependency boundary.
        raise DocumentReadError(f"Falha ao converter {path.name}: {type(exc).__name__}") from exc
    if not text.strip():
        raise DocumentReadError(
            f"Documento sem texto extraível: {path.name}. "
            "PDFs digitalizados precisam de OCR, ainda não disponível nesta configuração."
        )
    return text


def from_path(path: Path) -> SourceDocument:
    path = path.resolve()
    if not path.is_file():
        raise DocumentReadError(f"Arquivo não encontrado: {path}")
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise DocumentReadError(f"Formato não suportado: {suffix or 'sem extensão'}")
    if path.stat().st_size > MAX_BYTES:
        raise DocumentReadError("O documento excede o limite de 10 MB.")
    try:
        if suffix in TEXT_SUFFIXES:
            text = path.read_text(encoding="utf-8")
            return SourceDocument(path.name, text)
        return SourceDocument(path.name, _docling_extract(path), CONVERTED_MARKDOWN)
    except (OSError, UnicodeError) as exc:
        raise DocumentReadError(f"Falha ao ler {path.name}: {exc}") from exc


def from_bytes(filename: str, data: bytes) -> SourceDocument:
    """Read uploaded files without trusting paths included in the filename."""
    safe_name = Path(filename.replace("\\", "/")).name
    suffix = Path(safe_name).suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise DocumentReadError("Formato não suportado.")
    if len(data) > MAX_BYTES:
        raise DocumentReadError("O documento excede o limite de 10 MB.")
    if suffix in TEXT_SUFFIXES:
        try:
            return SourceDocument(safe_name, data.decode("utf-8"))
        except UnicodeError as exc:
            raise DocumentReadError("Arquivo texto deve estar codificado em UTF-8.") from exc
    with TemporaryDirectory(prefix="docdiff-") as folder:
        path = Path(folder) / f"input{suffix}"
        path.write_bytes(data)
        return SourceDocument(safe_name, _docling_extract(path), CONVERTED_MARKDOWN)
