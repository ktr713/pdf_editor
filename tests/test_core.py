from pathlib import Path

import fitz
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QGraphicsTextItem

from app.commands.element_commands import AddElementsCommand
from app.main_window import create_page_number_element
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


def test_page_number_is_inserted_only_on_reference_page(tmp_path: Path):
    source = tmp_path / "source.pdf"
    doc = fitz.open(); doc.new_page(width=300, height=400); doc.new_page(width=600, height=800); doc.save(source); doc.close()
    model = PdfService().load(source)
    element = create_page_number_element(model, 0, 8, 10, (0, 0, 0), None)
    assert element.page_index == 0
    assert element.text == "8"
    assert element.page_number_start == 8


def test_copy_element_preserves_position_and_uses_new_ids(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    source = tmp_path / "source.pdf"
    doc = fitz.open(); doc.new_page(); doc.new_page(); doc.save(source); doc.close()
    model = PdfService().load(source); original = TextElement(0, 33, 44, 100, 20, text="Footer")
    model.add_element(original)
    from app.main_window import MainWindow
    window = MainWindow(); window.model = model; window.view.model = model
    window.apply_element_to_all_pages(original)
    copied = model.pages[1].elements[0]
    assert (copied.x_pt, copied.y_pt) == (33, 44)
    assert copied.id != original.id
    model.modified = False
    window.close()


def test_page_number_expands_after_positioning(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    source = tmp_path / "source.pdf"
    doc = fitz.open(); doc.new_page(); doc.new_page(); doc.new_page(); doc.save(source); doc.close()
    model = PdfService().load(source)
    original = create_page_number_element(model, 0, 5, 10, (0, 0, 0), None)
    original.x_pt, original.y_pt = 77, 88
    model.add_element(original)
    from app.main_window import MainWindow
    window = MainWindow(); window.model = model; window.view.model = model
    window.apply_element_to_all_pages(original)
    assert [page.elements[0].text for page in model.pages] == ["5", "6", "7"]
    assert {(page.elements[0].x_pt, page.elements[0].y_pt) for page in model.pages} == {(77, 88)}
    model.modified = False
    window.close()
