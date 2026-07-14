from dataclasses import dataclass, field
from pathlib import Path

from app.models.element_model import ElementModel


@dataclass
class PageModel:
    page_index: int
    width_pt: float
    height_pt: float
    elements: list[ElementModel] = field(default_factory=list)


@dataclass
class DocumentModel:
    source_path: Path
    page_count: int
    pages: list[PageModel]
    modified: bool = False

    def find_element(self, element_id: str) -> ElementModel | None:
        """Return an element by identifier."""
        return next((e for p in self.pages for e in p.elements if e.id == element_id), None)

    def add_element(self, element: ElementModel) -> None:
        """Add an element to its page."""
        self.pages[element.page_index].elements.append(element)
        self.modified = True

    def remove_element(self, element: ElementModel) -> None:
        """Remove an element from its page."""
        self.pages[element.page_index].elements.remove(element)
        self.modified = True
