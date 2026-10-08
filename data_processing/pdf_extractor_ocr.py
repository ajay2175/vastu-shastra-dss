"""
Enhanced Vastu Shastra PDF Extraction with OCR Support
========================================================

Extends pdf_extractor.py with OCR capabilities for scanned image-based PDFs
Uses pytesseract + PIL for text extraction from scanned documents

This module provides:
- Fallback to OCR when pdfplumber extracts 0 characters
- Image preprocessing for better OCR accuracy
- Devanagari text recognition
- Progress tracking for large scans
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image
import io

logger = logging.getLogger(__name__)

try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
    logger.warning("pytesseract not available - OCR functionality disabled")

try:
    import pdfplumber
except ImportError:
    raise ImportError("pdfplumber required: pip install pdfplumber")

from pdf_extractor import VastuPDFExtractor, ExtractedText


class VastuPDFExtractorWithOCR(VastuPDFExtractor):
    """Enhanced extractor with OCR support for scanned PDFs"""

    def __init__(self, enable_ocr: bool = True, ocr_languages: str = "eng+san"):
        """
        Initialize OCR-enabled extractor

        Args:
            enable_ocr: Enable OCR for image-based PDFs
            ocr_languages: Tesseract languages (eng, san for Sanskrit, etc.)
        """
        super().__init__()
        self.enable_ocr = enable_ocr and PYTESSERACT_AVAILABLE
        self.ocr_languages = ocr_languages

        if self.enable_ocr:
            logger.info(f"✅ OCR enabled for languages: {ocr_languages}")
        else:
            logger.warning("⚠️  OCR disabled (pytesseract not available)")

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR accuracy

        Args:
            image: PIL Image object

        Returns:
            Preprocessed image
        """
        try:
            # Convert to grayscale if needed
            if image.mode != 'L':
                image = image.convert('L')

            # Resize for better OCR (upscale if too small)
            width, height = image.size
            if width < 800 or height < 600:
                scale_factor = max(800 / width, 600 / height)
                new_size = (int(width * scale_factor), int(height * scale_factor))
                image = image.resize(new_size, Image.Resampling.LANCZOS)

            # Apply contrast enhancement (optional - may not always help)
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.2)

            return image
        except Exception as e:
            logger.warning(f"Image preprocessing failed: {e}")
            return image

    def extract_text_from_pdf_page(self, pdf_path: Path, page_num: int) -> Optional[str]:
        """
        Extract text from a single PDF page using OCR

        Args:
            pdf_path: Path to PDF
            page_num: Page number (0-indexed)

        Returns:
            Extracted text or None
        """
        if not self.enable_ocr:
            return None

        try:
            with pdfplumber.open(pdf_path) as pdf:
                if page_num >= len(pdf.pages):
                    return None

                page = pdf.pages[page_num]
                image = page.to_image()

                # Convert PIL Image to format suitable for pytesseract
                if hasattr(image, 'original_image'):
                    pil_image = image.original_image
                else:
                    pil_image = image

                # Preprocess image
                pil_image = self._preprocess_image(pil_image)

                # Extract text using OCR
                text = pytesseract.image_to_string(
                    pil_image,
                    lang=self.ocr_languages
                )
                return text if text.strip() else None

        except Exception as e:
            logger.warning(f"OCR failed for page {page_num} of {pdf_path.name}: {e}")
            return None

    def extract_pdf_with_ocr_fallback(self, pdf_path: Path) -> ExtractedText:
        """
        Extract PDF text, falling back to OCR if needed

        Args:
            pdf_path: Path to PDF file

        Returns:
            ExtractedText with OCR metadata
        """
        # First try standard text extraction
        result = self.extract_pdf(pdf_path)

        # If no text extracted and OCR enabled, try OCR on sample pages
        if result.char_count == 0 and self.enable_ocr and result.total_pages > 0:
            logger.info(f"No text found in {pdf_path.name}, attempting OCR...")

            ocr_texts = []
            ocr_pages_processed = 0
            sample_size = min(5, result.total_pages)  # Sample first 5 pages

            for page_num in range(0, result.total_pages, max(1, result.total_pages // sample_size)):
                try:
                    page_text = self.extract_text_from_pdf_page(pdf_path, page_num)
                    if page_text:
                        ocr_texts.append(page_text)
                        ocr_pages_processed += 1
                except Exception as e:
                    logger.warning(f"OCR failed for page {page_num}: {e}")
                    continue

            if ocr_texts:
                result.extracted_text = "\n".join(ocr_texts)
                result.char_count = len(result.extracted_text)
                result.metadata['ocr_used'] = True
                result.metadata['ocr_pages'] = ocr_pages_processed
                logger.info(f"✅ OCR extracted {ocr_pages_processed} sample pages: {result.char_count} chars")

        return result


async def main_with_ocr():
    """
    Main extraction pipeline with OCR support
    """
    extractor = VastuPDFExtractorWithOCR(enable_ocr=True)

    # Source directory
    source_dir = Path(
        "~/Library/CloudStorage/OneDrive-ALPHASENSETECHNOLOGY(INDIA)PRIVATELIMITED/Personal/Vastu shastra"
    ).expanduser()

    # Output directories
    output_base = Path("~/vastu_shastra_dss/data").expanduser()
    ocr_texts_dir = output_base / "raw_texts_ocr"

    logger.info(f"Starting OCR-enhanced extraction from: {source_dir}")
    logger.info(f"Output directory: {ocr_texts_dir}")

    # Extract all PDFs with OCR fallback
    pdf_files = sorted(source_dir.glob('*.pdf'))
    results = []

    for idx, pdf_path in enumerate(pdf_files, 1):
        try:
            result = extractor.extract_pdf_with_ocr_fallback(pdf_path)
            results.append(result)

            if idx % 10 == 0:
                logger.info(f"Progress: {idx}/{len(pdf_files)} files processed")

        except Exception as e:
            logger.error(f"Error processing {pdf_path.name}: {e}")

    # Save results
    manifest_path = extractor.save_manifest(results, extractor.extraction_stats, ocr_texts_dir)
    saved_files = extractor.save_extracted_texts(results, ocr_texts_dir)

    logger.info(f"\n✅ OCR extraction pipeline complete!")
    logger.info(f"Manifest: {manifest_path}")
    logger.info(f"Texts saved: {len(saved_files)} files")

    return results, extractor.extraction_stats


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('/tmp/vastu_ocr_extraction.log'),
            logging.StreamHandler()
        ]
    )

    logger = logging.getLogger(__name__)

    if not PYTESSERACT_AVAILABLE:
        logger.warning("⚠️  OCR module requires pytesseract installation")
        logger.warning("Install with: pip install pytesseract pillow pdf2image")
        logger.warning("Also requires tesseract-ocr system package")

    # Run OCR extraction
    results, stats = asyncio.run(main_with_ocr())

    # Print summary
    print("\n" + "=" * 80)
    print("OCR EXTRACTION SUMMARY")
    print("=" * 80)
    print(f"Total Files: {stats['total_files']}")
    print(f"Successful: {stats['successful']}")
    print(f"Failed: {stats['failed']}")
    print(f"Total Characters: {stats['total_chars']:,}")
    print(f"OCR-Enhanced Texts: {sum(1 for r in results if r.metadata.get('ocr_used'))}")
    print("=" * 80)
