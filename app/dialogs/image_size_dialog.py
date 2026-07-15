from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QVBoxLayout,
)


class ImageSizeDialog(QDialog):
    def __init__(self, width_pt: float, height_pt: float, keep_aspect_ratio: bool, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("画像サイズ")

        self._aspect_ratio = width_pt / height_pt if height_pt > 0 else 1.0
        self.width = self._size_input(width_pt)
        self.height = self._size_input(height_pt)
        self.keep_aspect_ratio = QCheckBox("縦横比を維持する")
        self.keep_aspect_ratio.setChecked(keep_aspect_ratio)

        form = QFormLayout()
        form.addRow("幅 (pt)", self.width)
        form.addRow("高さ (pt)", self.height)
        form.addRow("", self.keep_aspect_ratio)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

        self.width.valueChanged.connect(self._width_changed)
        self.height.valueChanged.connect(self._height_changed)

    @staticmethod
    def _size_input(value: float) -> QDoubleSpinBox:
        control = QDoubleSpinBox()
        control.setRange(1.0, 10000.0)
        control.setDecimals(1)
        control.setSuffix(" pt")
        control.setValue(value)
        return control

    def _width_changed(self, value: float) -> None:
        if not self.keep_aspect_ratio.isChecked():
            return
        self.height.blockSignals(True)
        self.height.setValue(value / self._aspect_ratio)
        self.height.blockSignals(False)

    def _height_changed(self, value: float) -> None:
        if not self.keep_aspect_ratio.isChecked():
            return
        self.width.blockSignals(True)
        self.width.setValue(value * self._aspect_ratio)
        self.width.blockSignals(False)

    def values(self) -> tuple[float, float, bool]:
        return self.width.value(), self.height.value(), self.keep_aspect_ratio.isChecked()
