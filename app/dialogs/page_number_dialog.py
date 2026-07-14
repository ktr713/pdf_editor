from PySide6.QtGui import QColor
from PySide6.QtWidgets import QColorDialog, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QPushButton, QSpinBox


class PageNumberDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("ページ番号の追加")
        self.start_number = QSpinBox(); self.start_number.setRange(-999999, 999999); self.start_number.setValue(1)
        self.size = QDoubleSpinBox(); self.size.setRange(4, 200); self.size.setValue(10)
        self.color = QColor("black")
        color_button = QPushButton("色を選択"); color_button.clicked.connect(self._choose_color)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        layout = QFormLayout(self)
        layout.addRow("開始番号", self.start_number); layout.addRow("サイズ (pt)", self.size); layout.addRow("文字色", color_button); layout.addRow(buttons)

    def _choose_color(self) -> None:
        selected = QColorDialog.getColor(self.color, self)
        if selected.isValid(): self.color = selected
