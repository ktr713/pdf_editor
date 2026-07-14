import logging
from pathlib import Path


def configure_logging() -> None:
    """Configure rotating-safe basic application logging."""
    log_dir = Path.home() / ".pdf_overlay_editor" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=log_dir / "pdf_editor.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
