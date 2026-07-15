from pathlib import Path

from app.commands.element_commands import ResizeElementCommand
from app.models.document_model import DocumentModel, PageModel
from app.models.element_model import ImageElement


def test_resize_element_command_supports_undo_and_redo() -> None:
    model = DocumentModel(Path("source.pdf"), 1, [PageModel(0, 595.0, 842.0)])
    element = ImageElement(0, 10.0, 20.0, 100.0, 50.0, keep_aspect_ratio=True)
    model.add_element(element)
    model.modified = False
    refresh_count = 0

    def refresh() -> None:
        nonlocal refresh_count
        refresh_count += 1

    command = ResizeElementCommand(
        model,
        element,
        (100.0, 50.0, True),
        (240.0, 90.0, False),
        refresh,
    )

    command.redo()
    assert (element.width_pt, element.height_pt, element.keep_aspect_ratio) == (240.0, 90.0, False)
    assert model.modified is True

    model.modified = False
    command.undo()
    assert (element.width_pt, element.height_pt, element.keep_aspect_ratio) == (100.0, 50.0, True)
    assert model.modified is True
    assert refresh_count == 2
