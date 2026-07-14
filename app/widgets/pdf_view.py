from pathlib import Path

from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QImage, QPen, QPixmap
from PySide6.QtWidgets import QGraphicsItem, QGraphicsPixmapItem, QGraphicsScene, QGraphicsTextItem, QGraphicsView

from app.models.document_model import DocumentModel
from app.models.element_model import ImageElement, TextElement
from app.services.pdf_service import PdfService


class PdfView(QGraphicsView):
    PAGE_MARGIN = 24

    element_moved = Signal(object, object, object)
    selection_changed = Signal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.scene = QGraphicsScene(self); self.setScene(self.scene)
        self.model: DocumentModel | None = None; self.page_index = 0; self.zoom = 1.0
        self.service = PdfService(); self._items = {}
        self.setBackgroundBrush(QBrush(QColor(216, 216, 216)))
        self.setRenderHints(self.renderHints() | self.renderHints().Antialiasing | self.renderHints().SmoothPixmapTransform)
        self.scene.selectionChanged.connect(self._selection)

    def set_document(self, model: DocumentModel, page_index: int = 0) -> None:
        self.model, self.page_index = model, page_index; self.refresh()

    def refresh(self) -> None:
        self.scene.clear(); self._items.clear()
        if not self.model: return
        data, width, height, stride = self.service.render(self.model.source_path, self.page_index, self.zoom)
        image = QImage(data, width, height, stride, QImage.Format_RGB888).copy()
        bg = self.scene.addPixmap(QPixmap.fromImage(image)); bg.setZValue(-1)
        border = self.scene.addRect(0, 0, width, height, QPen(QColor(96, 96, 96), 1)); border.setZValue(-0.5)
        for element in self.model.pages[self.page_index].elements:
            if isinstance(element, TextElement):
                item = QGraphicsTextItem(element.text); font = item.font(); font.setPointSizeF(element.font_size_pt * self.zoom); item.setFont(font); item.setDefaultTextColor(QColor(*element.color))
            elif isinstance(element, ImageElement) and element.image_path:
                pix = QPixmap(str(element.image_path)).scaled(round(element.width_pt*self.zoom), round(element.height_pt*self.zoom), Qt.KeepAspectRatio, Qt.SmoothTransformation); item = QGraphicsPixmapItem(pix)
            else: continue
            item.setPos(element.x_pt*self.zoom, element.y_pt*self.zoom); item.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable); item.setData(0, element.id); item.setData(1, QPointF(item.pos())); self.scene.addItem(item); self._items[element.id] = item
        margin = self.PAGE_MARGIN
        self.scene.setSceneRect(-margin, -margin, width + margin * 2, height + margin * 2)

    def mouseReleaseEvent(self, event) -> None:
        item = self.itemAt(event.position().toPoint())
        super().mouseReleaseEvent(event)
        self._commit_item_move(item)

    def _commit_item_move(self, item) -> None:
        if item and item.data(0) and self.model:
            element = self.model.find_element(item.data(0)); old = item.data(1); new = item.pos()
            if element and old != new:
                item.setData(1, QPointF(new))
                self.element_moved.emit(element, (old.x()/self.zoom, old.y()/self.zoom), (new.x()/self.zoom, new.y()/self.zoom))

    def _selection(self) -> None:
        selected = self.scene.selectedItems()
        self.selection_changed.emit(self.model.find_element(selected[0].data(0)) if selected and self.model else None)
