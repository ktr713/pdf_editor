from pathlib import Path

import fitz
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QGraphicsTextItem

from app.models.element_model import ImageElement, TextElement
from app.services.coordinate_service import CoordinateService
from app.services.pdf_service import PdfService
from app.services.save_service import SaveService
from app.widgets.pdf_view import PdfView


def test_coordinates():
    assert CoordinateService.view_to_pdf(210, 420, 2, 10, 20) == (100, 200)
    assert CoordinateService.pdf_to_view(100, 200, 2, 10, 20) == (210, 420)


def test_load_and_save_text(tmp_path: Path):
    source = tmp_path / "source.pdf"
    doc = fitz.open(); doc.new_page(width=300, height=400); doc.save(source); doc.close()
    model = PdfService().load(source)
    model.add_element(TextElement(0, 20, 30, 100, 20, text="Hello", font_size_pt=12))
    output = tmp_path / "output.pdf"; SaveService().save(model, output)
    with fitz.open(output) as result:
        assert "Hello" in result[0].get_text()


def test_pdf_view_shows_page_boundary_and_text_color(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    source = tmp_path / "source.pdf"
    doc = fitz.open(); doc.new_page(width=300, height=400); doc.save(source); doc.close()
    model = PdfService().load(source)
    element = TextElement(0, 20, 30, 100, 20, text="Color", color=(12, 34, 56))
    model.add_element(element)

    view = PdfView()
    view.set_document(model)

    assert view.backgroundBrush().color() == QColor(216, 216, 216)
    assert view.scene.sceneRect().left() < 0
    assert view.scene.sceneRect().top() < 0
    item = view._items[element.id]
    assert isinstance(item, QGraphicsTextItem)
    assert item.defaultTextColor() == QColor(12, 34, 56)
    view.close()
