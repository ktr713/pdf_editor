import logging
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence, QUndoStack
from PySide6.QtWidgets import QFileDialog, QListWidget, QMainWindow, QMessageBox, QSplitter, QStatusBar, QToolBar

from app.commands.element_commands import AddElementCommand, AddElementsCommand, DeleteElementCommand, MoveElementCommand
from app.dialogs.page_number_dialog import PageNumberDialog
from app.dialogs.text_dialog import TextDialog
from app.models.document_model import DocumentModel
from app.models.element_model import ImageElement, TextElement
from app.services.font_service import FontService
from app.services.pdf_service import PdfService
from app.services.save_service import SaveService
from app.widgets.pdf_view import PdfView

log = logging.getLogger(__name__)


def create_page_number_element(model: DocumentModel, reference_page_index: int, start: int, size: float, color: tuple[int, int, int], font_file):
    texts = [str(start + offset) for offset in range(model.page_count)]
    width = max(40.0, max(map(len, texts)) * size)
    reference = model.pages[reference_page_index]
    x = (reference.width_pt - width) / 2
    y = reference.height_pt - size * 2
    return TextElement(reference_page_index, x, y, width, size * 1.4, text=texts[reference_page_index], font_file=font_file, font_size_pt=size, color=color, alignment="center", page_number_start=start)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__(); self.setWindowTitle("PDF Overlay Editor"); self.resize(1200, 800)
        self.model: DocumentModel | None = None; self.selected = None; self.pdf = PdfService(); self.saver = SaveService(); self.undo = QUndoStack(self)
        self.pages = QListWidget(); self.pages.setMaximumWidth(150); self.view = PdfView(); self.view.element_moved.connect(self._move); self.view.selection_changed.connect(lambda e: setattr(self, "selected", e)); self.view.apply_to_all_pages_requested.connect(self.apply_element_to_all_pages); self.pages.currentRowChanged.connect(self._show_page)
        splitter = QSplitter(); splitter.addWidget(self.pages); splitter.addWidget(self.view); splitter.setStretchFactor(1, 1); self.setCentralWidget(splitter); self.setStatusBar(QStatusBar())
        self._actions(); self._menus(); self._toolbar(); self._update_title()

    def _actions(self) -> None:
        self.open_action = QAction("開く", self, shortcut=QKeySequence.Open, triggered=self.open_pdf)
        self.save_action = QAction("上書き保存", self, shortcut=QKeySequence.Save, triggered=self.save)
        self.save_as_action = QAction("名前を付けて保存", self, shortcut=QKeySequence.SaveAs, triggered=self.save_as)
        self.text_action = QAction("文字追加", self, triggered=self.add_text); self.image_action = QAction("画像追加", self, triggered=self.add_image)
        self.page_number_action = QAction("ページ番号追加", self, triggered=self.add_page_numbers)
        self.delete_action = QAction("削除", self, shortcut=QKeySequence.Delete, triggered=self.delete_selected)
        self.undo_action = self.undo.createUndoAction(self, "元に戻す"); self.undo_action.setShortcut(QKeySequence.Undo)
        self.redo_action = self.undo.createRedoAction(self, "やり直す"); self.redo_action.setShortcut(QKeySequence.Redo)
        self.zoom_in_action = QAction("拡大", self, shortcut=QKeySequence.ZoomIn, triggered=lambda: self._zoom(1.25)); self.zoom_out_action = QAction("縮小", self, shortcut=QKeySequence.ZoomOut, triggered=lambda: self._zoom(.8))

    def _menus(self) -> None:
        file = self.menuBar().addMenu("ファイル"); file.addActions([self.open_action, self.save_action, self.save_as_action]); file.addSeparator(); file.addAction("終了", self.close)
        edit = self.menuBar().addMenu("編集"); edit.addActions([self.undo_action, self.redo_action, self.delete_action])
        insert = self.menuBar().addMenu("挿入"); insert.addActions([self.text_action, self.image_action, self.page_number_action])
        view = self.menuBar().addMenu("表示"); view.addActions([self.zoom_in_action, self.zoom_out_action])

    def _toolbar(self) -> None:
        bar = QToolBar(); self.addToolBar(bar); bar.addActions([self.open_action, self.save_action, self.save_as_action]); bar.addSeparator(); bar.addActions([self.undo_action, self.redo_action]); bar.addSeparator(); bar.addActions([self.text_action, self.image_action, self.page_number_action, self.delete_action])

    def open_pdf(self) -> None:
        if not self._confirm_discard(): return
        path, _ = QFileDialog.getOpenFileName(self, "PDFを開く", "", "PDF (*.pdf)")
        if not path: return
        try:
            self.model = self.pdf.load(Path(path)); self.undo.clear(); self.pages.clear(); self.pages.addItems([f"ページ {i+1}" for i in range(self.model.page_count)]); self.pages.setCurrentRow(0); log.info("PDF opened: %s", path); self._update_title()
        except Exception as exc: log.exception("Open failed"); QMessageBox.critical(self, "読み込みエラー", f"PDFファイルを開けませんでした。\n\n{exc}")

    def add_text(self) -> None:
        if not self.model: return
        dialog = TextDialog(self)
        if dialog.exec() and dialog.text.text():
            pages = self.model.pages if dialog.scope.currentData() == "all_pages" else [self.model.pages[self.view.page_index]]
            color = dialog.color; font_file = FontService().find_default_japanese_font()
            elements = [TextElement(page.page_index, page.width_pt/2-50, page.height_pt/2, 100, dialog.size.value()*1.4, text=dialog.text.text(), font_file=font_file, font_size_pt=dialog.size.value(), color=(color.red(), color.green(), color.blue())) for page in pages]
            self.undo.push(AddElementsCommand(self.model, elements, self._refresh) if len(elements) > 1 else AddElementCommand(self.model, elements[0], self._refresh))

    def add_image(self) -> None:
        if not self.model: return
        path, _ = QFileDialog.getOpenFileName(self, "画像を選択", "", "画像 (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)")
        if not path: return
        try:
            with Image.open(path) as image: image.verify(); width, height = image.size
            all_pages = QMessageBox.question(self, "適用範囲", "すべてのページに画像を追加しますか？", QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes
            pages = self.model.pages if all_pages else [self.model.pages[self.view.page_index]]
            elements = []
            for page in pages:
                max_width = min(180.0, page.width_pt*.4); scale = max_width/width
                elements.append(ImageElement(page.page_index, (page.width_pt-max_width)/2, (page.height_pt-height*scale)/2, max_width, height*scale, image_path=Path(path)))
            self.undo.push(AddElementsCommand(self.model, elements, self._refresh) if len(elements) > 1 else AddElementCommand(self.model, elements[0], self._refresh))
        except Exception as exc: log.exception("Image failed"); QMessageBox.critical(self, "画像エラー", f"画像を読み込めませんでした。\n\n{exc}")

    def add_page_numbers(self) -> None:
        if not self.model: return
        dialog = PageNumberDialog(self)
        if not dialog.exec(): return
        color = dialog.color; size = dialog.size.value(); start = dialog.start_number.value(); font_file = FontService().find_default_japanese_font()
        element = create_page_number_element(self.model, self.view.page_index, start, size, (color.red(), color.green(), color.blue()), font_file)
        self.undo.push(AddElementCommand(self.model, element, self._refresh))
        self.statusBar().showMessage("ページ番号を配置後、右クリックして「すべてのページに適用」してください", 8000)

    def apply_element_to_all_pages(self, element) -> None:
        if not self.model: return
        elements = []
        for page in self.model.pages:
            if page.page_index == element.page_index: continue
            changes = {"page_index": page.page_index, "id": str(uuid4())}
            if isinstance(element, TextElement) and element.page_number_start is not None:
                changes["text"] = str(element.page_number_start + page.page_index)
            elements.append(replace(element, **changes))
        if elements:
            self.undo.push(AddElementsCommand(self.model, elements, self._refresh, "すべてのページに適用"))
            self.statusBar().showMessage(f"{len(elements)}ページに適用しました", 5000)

    def delete_selected(self) -> None:
        if self.model and self.selected: self.undo.push(DeleteElementCommand(self.model, self.selected, self._refresh)); self.selected = None

    def _move(self, element, old, new) -> None:
        if self.model: self.undo.push(MoveElementCommand(self.model, element, old, new, self._refresh))

    def _show_page(self, index: int) -> None:
        if self.model and index >= 0: self.view.set_document(self.model, index); self.statusBar().showMessage(f"Page {index+1} / {self.model.page_count}   Zoom: {self.view.zoom*100:.0f}%")

    def _zoom(self, factor: float) -> None:
        self.view.zoom = min(4, max(.25, self.view.zoom*factor)); self._refresh()

    def _refresh(self) -> None:
        self.view.refresh(); self._update_title()

    def save(self) -> bool:
        return self._save_to(self.model.source_path) if self.model else False

    def save_as(self) -> bool:
        if not self.model: return False
        path, _ = QFileDialog.getSaveFileName(self, "名前を付けて保存", str(self.model.source_path), "PDF (*.pdf)")
        return self._save_to(Path(path)) if path else False

    def _save_to(self, path: Path) -> bool:
        try: self.saver.save(self.model, path); self._update_title(); QMessageBox.information(self, "保存完了", "PDFを保存しました。"); return True
        except Exception as exc: log.exception("Save failed"); QMessageBox.critical(self, "保存エラー", f"PDFを保存できませんでした。元ファイルは変更されていません。\n\n{exc}"); return False

    def _confirm_discard(self) -> bool:
        if not self.model or not self.model.modified: return True
        result = QMessageBox.question(self, "未保存の変更", "変更内容が保存されていません。保存しますか？", QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
        return self.save() if result == QMessageBox.Save else result == QMessageBox.Discard

    def _update_title(self) -> None:
        name = self.model.source_path.name if self.model else "PDF Overlay Editor"; mark = " *" if self.model and self.model.modified else ""; self.setWindowTitle(name + mark)

    def closeEvent(self, event: QCloseEvent) -> None:
        event.accept() if self._confirm_discard() else event.ignore()
