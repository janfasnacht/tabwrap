# tex_compiler/utils/image_processing.py
import logging
from pathlib import Path
from typing import Optional
import numpy as np
from PIL import Image
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


def convert_pdf_to_cropped_png(
    pdf_path: Path,
    output_dir: Path,
    suffix: str = "",
    dpi: int = 300,
    padding: int = 10
) -> Optional[Path]:
    """Convert PDF to cropped PNG with white space removal."""
    try:
        base_name = pdf_path.stem
        if suffix in base_name:
            png_path = output_dir / f"{base_name}.png"
        else:
            png_path = output_dir / f"{base_name}{suffix}.png"

        logger.info(f"Starting PDF to PNG conversion from: {pdf_path} to: {png_path}")

        doc = fitz.open(str(pdf_path))
        page = doc.load_page(0)
        logger.info("PDF opened successfully")

        matrix = fitz.Matrix(dpi/72, dpi/72)
        pix = page.get_pixmap(matrix=matrix)
        logger.info("Page rendered to pixmap")

        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
            pix.height, pix.width, pix.n
        )
        logger.info(f"Image array shape: {img.shape}")
        logger.info(f"Saving PNG to: {png_path}")

        mask = np.all(img < 250, axis=-1)
        coords = np.argwhere(mask)

        if len(coords) == 0:
            y0, x0, y1, x1 = 0, 0, pix.height, pix.width
        else:
            y0, x0 = coords.min(axis=0)
            y1, x1 = coords.max(axis=0) + 1

        x0 = max(0, x0 - padding)
        y0 = max(0, y0 - padding)
        x1 = min(pix.width, x1 + padding)
        y1 = min(pix.height, y1 + padding)

        cropped_img = img[y0:y1, x0:x1]
        pil_img = Image.fromarray(cropped_img)
        pil_img.save(str(png_path))
        logger.info(f"PNG saved successfully: {png_path.exists()}")

        doc.close()
        return png_path

    except Exception as e:
        logger.error(f"Error converting PDF to PNG: {e}")
        return None