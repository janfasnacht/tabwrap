# tex_compiler/utils/image_processing.py
import logging
import subprocess
from pathlib import Path

import fitz  # PyMuPDF
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


def convert_pdf_to_cropped_png(
    pdf_path: Path, output_dir: Path, suffix: str = "", dpi: int = 300, padding: int = 10
) -> Path | None:
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

        matrix = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=matrix)
        logger.info("Page rendered to pixmap")

        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
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


def convert_pdf_to_svg(pdf_path: Path, output_dir: Path, suffix: str = "") -> Path | None:
    """Convert PDF to SVG using pdf2svg."""
    try:
        base_name = pdf_path.stem
        if suffix in base_name:
            svg_path = output_dir / f"{base_name}.svg"
        else:
            svg_path = output_dir / f"{base_name}{suffix}.svg"

        logger.info(f"Starting PDF to SVG conversion from: {pdf_path} to: {svg_path}")

        # Check if pdf2svg is available
        try:
            subprocess.run(["pdf2svg", "--help"], capture_output=True)
        except FileNotFoundError:
            raise RuntimeError(
                "pdf2svg not found. Install with: brew install pdf2svg (macOS) or sudo apt-get install pdf2svg (Ubuntu)"
            )

        # Convert PDF to SVG (first page only)
        subprocess.run(["pdf2svg", str(pdf_path), str(svg_path), "1"], capture_output=True, text=True, check=True)

        if svg_path.exists():
            logger.info(f"SVG saved successfully: {svg_path}")
            return svg_path
        else:
            logger.error("SVG file was not created")
            return None

    except subprocess.CalledProcessError as e:
        logger.error(f"pdf2svg failed: {e.stderr}")
        return None
    except Exception as e:
        logger.error(f"Error converting PDF to SVG: {e}")
        return None
