import os
from pathlib import Path

import fitz

from app.models.document_model import DocumentModel
from app.models.element_model import ImageElement, TextElement


class SaveService:
    def save(self, model: DocumentModel, destination: Path) -> None:
        """Write all overlays to a new PDF and atomically replace destination when needed."""
        source = model.source_path.resolve()
        destination = destination.resolve()
        overwrite = source == destination
        temp = destination.with_name(f".{destination.stem}.editing.tmp.pdf") if overwrite else destination
        try:
            with fitz.open(source) as doc:
                for page_model in model.pages:
                    page = doc.load_page(page_model.page_index)
                    for element in page_model.elements:
                        if not element.visible:
                            continue
                        if isinstance(element, TextElement):
                            kwargs = {}
                            if element.font_file:
                                kwargs["fontfile"] = str(element.font_file)
                                kwargs["fontname"] = f"overlay_{element.id.replace('-', '')[:8]}"
                            page.insert_text(
                                fitz.Point(element.x_pt, element.y_pt + element.font_size_pt),
                                element.text,
                                fontsize=element.font_size_pt,
                                color=tuple(c / 255 for c in element.color),
                                **kwargs,
                            )
                        elif isinstance(element, ImageElement) and element.image_path:
                            rect = fitz.Rect(element.x_pt, element.y_pt, element.x_pt + element.width_pt, element.y_pt + element.height_pt)
                            page.insert_image(rect, filename=str(element.image_path), keep_proportion=element.keep_aspect_ratio)
                doc.save(temp, garbage=4, deflate=True, clean=True)
            if overwrite:
                os.replace(temp, destination)
            model.source_path = destination
            model.modified = False
        except Exception:
            if overwrite and temp.exists():
                temp.unlink(missing_ok=True)
            raise
