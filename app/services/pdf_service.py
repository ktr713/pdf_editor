from pathlib import Path

import fitz

from app.models.document_model import DocumentModel, PageModel


class PdfService:
    def load(self, path: Path) -> DocumentModel:
        """Read page metadata from an unencrypted PDF."""
        with fitz.open(path) as doc:
            if doc.needs_pass:
                raise ValueError("Password-protected PDFs are not supported")
            pages = [PageModel(i, p.rect.width, p.rect.height) for i, p in enumerate(doc)]
        return DocumentModel(path, len(pages), pages)

    def render(self, path: Path, page_index: int, zoom: float) -> tuple[bytes, int, int, int]:
        """Render one page and return RGB bytes and dimensions."""
        with fitz.open(path) as doc:
            pix = doc.load_page(page_index).get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
            return pix.samples, pix.width, pix.height, pix.stride
