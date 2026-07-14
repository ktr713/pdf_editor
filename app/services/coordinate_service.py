class CoordinateService:
    @staticmethod
    def view_to_pdf(view_x: float, view_y: float, zoom: float, offset_x: float = 0, offset_y: float = 0) -> tuple[float, float]:
        """Convert view pixels to PDF points."""
        if zoom <= 0:
            raise ValueError("zoom must be positive")
        return (view_x - offset_x) / zoom, (view_y - offset_y) / zoom

    @staticmethod
    def pdf_to_view(pdf_x: float, pdf_y: float, zoom: float, offset_x: float = 0, offset_y: float = 0) -> tuple[float, float]:
        """Convert PDF points to view pixels."""
        if zoom <= 0:
            raise ValueError("zoom must be positive")
        return pdf_x * zoom + offset_x, pdf_y * zoom + offset_y
