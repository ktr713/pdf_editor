from PySide6.QtGui import QUndoCommand

from app.models.document_model import DocumentModel
from app.models.element_model import ElementModel


class AddElementCommand(QUndoCommand):
    def __init__(self, model: DocumentModel, element: ElementModel, refresh) -> None:
        super().__init__("要素を追加")
        self.model, self.element, self.refresh = model, element, refresh

    def redo(self) -> None:
        self.model.add_element(self.element)
        self.refresh()

    def undo(self) -> None:
        self.model.remove_element(self.element)
        self.refresh()


class AddElementsCommand(QUndoCommand):
    def __init__(self, model: DocumentModel, elements: list[ElementModel], refresh, text: str = "要素を一括追加") -> None:
        super().__init__(text)
        self.model, self.elements, self.refresh = model, elements, refresh

    def redo(self) -> None:
        for element in self.elements:
            self.model.add_element(element)
        self.refresh()

    def undo(self) -> None:
        for element in reversed(self.elements):
            self.model.remove_element(element)
        self.refresh()


class DeleteElementCommand(QUndoCommand):
    def __init__(self, model: DocumentModel, element: ElementModel, refresh) -> None:
        super().__init__("要素を削除")
        self.model, self.element, self.refresh = model, element, refresh

    def redo(self) -> None:
        self.model.remove_element(self.element)
        self.refresh()

    def undo(self) -> None:
        self.model.add_element(self.element)
        self.refresh()


class MoveElementCommand(QUndoCommand):
    def __init__(self, model: DocumentModel, element: ElementModel, old: tuple[float, float], new: tuple[float, float], refresh) -> None:
        super().__init__("要素を移動")
        self.model, self.element, self.old, self.new, self.refresh = model, element, old, new, refresh

    def _set(self, point: tuple[float, float]) -> None:
        self.element.x_pt, self.element.y_pt = point
        self.model.modified = True
        self.refresh()

    def redo(self) -> None:
        self._set(self.new)

    def undo(self) -> None:
        self._set(self.old)


class ResizeElementCommand(QUndoCommand):
    def __init__(self, model: DocumentModel, element: ElementModel, old: tuple[float, float], new: tuple[float, float], refresh) -> None:
        super().__init__("画像サイズを変更")
        self.model, self.element, self.old, self.new, self.refresh = model, element, old, new, refresh

    def _set(self, size: tuple[float, float]) -> None:
        self.element.width_pt, self.element.height_pt = size
        self.model.modified = True
        self.refresh()

    def redo(self) -> None:
        self._set(self.new)

    def undo(self) -> None:
        self._set(self.old)
