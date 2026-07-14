import os
from pathlib import Path


class FontService:
    CANDIDATES = ("YuGothR.ttc", "meiryo.ttc", "msgothic.ttc")

    def find_default_japanese_font(self) -> Path | None:
        """Find a common Windows Japanese font, if available."""
        font_dir = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
        return next((font_dir / name for name in self.CANDIDATES if (font_dir / name).exists()), None)
