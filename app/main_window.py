import logging
from pathlib import Path

from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence, QUndoStack
from PySide6.QtWidgets import QFileDialog, QListWidget, QMainWindow, QMessageBox, QSplitter, QStatusBar, QToolBar

from app.commands.element_commands import AddElementCommand, DeleteElementCommand, MoveElementCommand
from app.dialogs.text_dialog import TextDialog
from app.models.document_model import DocumentModel
from app.models.element_model import ImageElement, TextElement
from app.services.font_service import FontService
from app.services.pdf_service import PdfService
from app.services.save_service import SaveService
from app.widgets.pdf_view import PdfView

log = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__(); self.setWindowTitle("PDF Overlay Editor"); self.resize(1200, 800)
        self.model: DocumentModel | None = None; self.selected = None; self.pdf = PdfService(); self.saver = SaveService(); self.undo = QUndoStack(self)
        self.pages = QListWidget(); self.pages.setMaximumWidth(150); self.view = PdfView(); self.view.element_moved.connect(self._move); self.view.selection_changed.connect(lambda e: setattr(self, "selected", e)); self.pages.currentRowChanged.connect(self._show_page)
        splitter = QSplitter(); splitter.addWidget(self.pages); splitter.addWidget(self.view); splitter.setStretchFactor(1, 1); self.setCentralWidget(splitter); self.setStatusBar(QStatusBar())
        self._actions(); self._menus(); self._toolbar(); self._update_title()

    def _actions(self) -> None:
        self.open_action = QAction("開く", self, shortcut=QKeySequence.Open, triggered=self.open_pdf)
        self.save_action = QAction("上書き保存", self, shortcut=QKeySequence.Save, triggered=self.save)
        self.save_as_action = QAction("名前を付けて保存", self, shortcut=QKeySequence.SaveAs, triggered=self.save_as)
        self.text_action = QAction("文字追加", self, triggered=self.add_text); self.image_action = QAction("画像追加", self, triggered=self.add_image)
        self.delete_action = QAction("削除", self, shortcut=QKeySequence.Delete, triggered=self.delete_selected)
        self.undo_action = self.undo.createUndoAction(self, "元に戻す"); self.undo_action.setShortcut(QKeySequence.Undo)
        self.redo_action = self.undo.createRedoAction(self, "やり直す"); self.redo_action.setShortcut(QKeySequence.Redo)
        self.zoom_in_action = QAction("拡大", self, shortcut=QKeySequence.ZoomIn, triggered=lambda: self._zoom(1.25)); self.zoom_out_action = QAction("縮小", self, shortcut=QKeySequence.ZoomOut, triggered=lambda: self._zoom(.8))

    def _menus(self) -> None:
        file = self.menuBar().addMenu("ファイル"); file.addActions([self.open_action, self.save_action, self.save_as_action]); file.addSeparator(); file.addAction("終了", self.close)
        edit = self.menuBar().addMenu("編集"); edit.addActions([self.undo_action, self.redo_action, self.delete_action])
        insert = self.menuBar().addMenu("挿入"); insert.addActions([self.text_action, self.image_action])
        view = self.menuBar().addMenu("表示"); view.addActions([self.zoom_in_action, self.zoom_out_action])

    def _toolbar(self) -> None:
        bar = QToolBar(); self.addToolBar(bar); bar.addActions([self.open_action, self.save_action, self.save_as_action]); bar.addSeparator(); bar.addActions([self.undo_action, self.redo_action]); bar.addSeparator(); bar.addActions([self.text_action, self.image_action, self.delete_action])

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
            page = self.model.pages[self.view.page_index]; color = dialog.color
            element = TextElement(page.page_index, page.width_pt/2-50, page.height_pt/2, 100, dialog.size.value()*1.4, text=dialog.text.text(), font_file=FontService().find_default_japanese_font(), font_size_pt=dialog.size.value(), color=(color.red(), color.green(), color.blue()))
            self.undo.push(AddElementCommand(self.model, element, self._refresh))

    def add_image(self) -> None:
        if not self.model: return
        path, _ = QFileDialog.getOpenFileName(self, "画像を選択", "", "画像 (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)")
        if not path: return
        try:
            with Image.open(path) as image: image.verify(); width, height = image.size
            page = self.model.pages[self.view.page_index]; max_width = min(180.0, page.width_pt*.4); scale = max_width/width
            element = ImageElement(page.page_index, (page.width_pt-max_width)/2, (page.height_pt-height*scale)/2, max_width, height*scale, image_path=Path(path))
            self.undo.push(AddElementCommand(self.model, element, self._refresh))
        except Exception as exc: log.exception("Image failed"); QMessageBox.critical(self, "画像エラー", f"画像を読み込めませんでした。\n\n{exc}")

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
