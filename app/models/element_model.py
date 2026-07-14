from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from uuid import uuid4


class ApplyScope(Enum):
    CURRENT_PAGE = "current_page"
    ALL_PAGES = "all_pages"
    PAGE_RANGE = "page_range"


@dataclass
class ElementModel:
    page_index: int
    x_pt: float
    y_pt: float
    width_pt: float
    height_pt: float
    id: str = field(default_factory=lambda: str(uuid4()))
    visible: bool = True
    locked: bool = False


@dataclass
class TextElement(ElementModel):
    text: str = ""
    font_family: str = ""
    font_file: Path | None = None
    font_size_pt: float = 10.0
    color: tuple[int, int, int] = (0, 0, 0)
    alignment: str = "left"


@dataclass
class ImageElement(ElementModel):
    image_path: Path | None = None
    keep_aspect_ratio: bool = True
    opacity: float = 1.0
