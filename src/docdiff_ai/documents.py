"""Document input adapters; heavy extraction dependencies are optional."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from .core import SourceDocument

MAX_BYTES = 10 * 1024 * 1024
TEXT_SUFFIXES = {".txt", ".md"}
DOCLING_SUFFIXES = {".pdf", ".docx", ".pptx"}
SUPPORTED_SUFFIXES = TEXT_SUFFIXES | DOCLING_SUFFIXES


class DocumentReadError(ValueError):
    """Unsupported, unreadable, or oversized input document."""


def _docling_extract(path: Path) -> str:
    try:
        from docling.document_converter import DocumentConverter
    except ImportError as exc:
        raise DocumentReadError(
            "Instale a integração para PDF/Office com: pip install 'docdiff-ai[documents]'"
        ) from exc
    try:
        result = DocumentConverter().convert(str(path))
        text = result.document.export_to_markdown()
    except Exception as exc:
        raise DocumentReadError(f"Falha na conversão de {path.name}: {exc}") from exc
    if not text.strip():
        raise DocumentReadError(f"Não foi possível extrair conteúdo de {path.name}.")
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
        else:
            text = _docling_extract(path)
    except (OSError, UnicodeError) as exc:
        raise DocumentReadError(f"Falha ao ler {path.name}: {exc}") from exc
    return SourceDocument(path.name, text)


def from_bytes(filename: str, data: bytes) -> SourceDocument:
    """Read a user-uploaded file without trusting its original filesystem path."""
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
        return SourceDocument(safe_name, _docling_extract(path))
