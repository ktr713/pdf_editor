from pathlib import Path

import fitz
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QGraphicsTextItem

from app.commands.element_commands import AddElementsCommand
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


def test_move_signal_can_refresh_scene_without_using_deleted_item(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    source = tmp_path / "source.pdf"
    doc = fitz.open(); doc.new_page(width=300, height=400); doc.save(source); doc.close()
    model = PdfService().load(source); element = TextElement(0, 20, 30, 100, 20, text="Move")
    model.add_element(element); view = PdfView(); view.set_document(model)
    item = view._items[element.id]; item.setPos(40, 50)
    view.element_moved.connect(lambda *_: view.refresh())
    view._commit_item_move(item)
    assert (element.x_pt, element.y_pt) == (20, 30)
    view.close()


def test_add_elements_command_groups_all_pages(tmp_path: Path):
    source = tmp_path / "source.pdf"
    doc = fitz.open(); doc.new_page(); doc.new_page(); doc.save(source); doc.close()
    model = PdfService().load(source)
    elements = [TextElement(i, 10, 10, 40, 20, text=str(i + 5)) for i in range(2)]
    command = AddElementsCommand(model, elements, lambda: None)
    command.redo()
    assert [page.elements[0].text for page in model.pages] == ["5", "6"]
    command.undo()
    assert all(not page.elements for page in model.pages)
