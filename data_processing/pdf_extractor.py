"""
Vastu Shastra PDF Extraction Pipeline
=====================================

Extracts text from 100+ classical Vastu texts with preservation of:
- Chapter structure and hierarchy
- Verse numbers and section headings
- Sanskrit terms and Devanagari text
- Page numbers and metadata

Uses pdfplumber for robust text extraction and handles:
- Corrupted PDFs (skip with logging)
- Varying text formats
- Metadata parsing (title, author, period, tradition)
"""

import asyncio
import json
import logging
import re
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import traceback

try:
    import pdfplumber
except ImportError:
    raise ImportError("pdfplumber required: pip install pdfplumber")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/vastu_extraction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class Chapter:
    """Represents a chapter in a Vastu text"""
    num: int
    title: str
    text: str
    page_start: int = 1
    page_end: int = 1
    verse_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExtractedText:
    """Complete extracted Vastu text with metadata"""
    filename: str
    title: str
    author: Optional[str] = None
    period: Optional[str] = None  # ancient, medieval, modern
    tradition: Optional[str] = None  # North, South, Central
    total_pages: int = 0
    extracted_text: str = ""
    chapters: List[Chapter] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    extraction_status: str = "success"
    error_message: Optional[str] = None
    extraction_time: str = ""
    char_count: int = 0
    verse_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['chapters'] = [ch.to_dict() if isinstance(ch, Chapter) else ch for ch in self.chapters]
        return data


class VastuPDFExtractor:
    """Robust extractor for Vastu Shastra texts from PDFs"""

    # Text patterns for parsing
    CHAPTER_PATTERNS = [
        r'^(?:Chapter|अध्याय|Ch\.?)\s*(\d+)',
        r'^(?:CHAPTER|ADHYAYA)\s*(\d+)',
        r'^\s*(\d+)(?:\s*[.:]|\s*$)',
    ]

    VERSE_PATTERNS = [
        r'^\s*(?:Verse|श्लोक|Shloka|v\.?)\s*(\d+)',
        r'^(\d+)(?:\.|\)|\s*$)',
    ]

    SECTION_PATTERNS = [
        r'^(?:Section|खण्ड|Sec\.?|SECTION)\s*(.+?)(?:\n|$)',
        r'^(?:Part|भाग|PART)\s*([A-Za-z0-9]+)',
    ]

    # Known Vastu texts metadata
    KNOWN_TEXTS = {
        'Mayamatam': {'period': 'medieval', 'tradition': 'South', 'author': 'Bhoopal'},
        'Manasara': {'period': 'medieval', 'tradition': 'North', 'author': 'Unknown'},
        'Samarangana Sutradhara': {'period': 'medieval', 'tradition': 'North', 'author': 'Bhoja'},
        'Brihat Samhita': {'period': 'ancient', 'tradition': 'North', 'author': 'Varahamihira'},
        'Vishnu Dharmottara': {'period': 'ancient', 'tradition': 'South', 'author': 'Unknown'},
        'Aparajitapriccha': {'period': 'medieval', 'tradition': 'South', 'author': 'Unknown'},
        'Isana Shiva Gurudeva Paddhati': {'period': 'medieval', 'tradition': 'South', 'author': 'Isana Shiva Gurudeva'},
        'Silparatna': {'period': 'medieval', 'tradition': 'South', 'author': 'Vrajarama'},
        'Tantrasamuccaya': {'period': 'medieval', 'tradition': 'South', 'author': 'Bhaskara'},
        'Manushyalaya Chandrika': {'period': 'medieval', 'tradition': 'South', 'author': 'Unknown'},
    }

    def __init__(self):
        self.session_start = datetime.now().isoformat()
        self.extraction_stats = {
            'total_files': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'total_chars': 0,
            'total_pages': 0,
            'avg_pages_per_text': 0.0,
            'errors': []
        }

    def extract_pdf(self, pdf_path: Path) -> ExtractedText:
        """
        Extract text and metadata from a single PDF

        Args:
            pdf_path: Path to PDF file

        Returns:
            ExtractedText with all extracted data
        """
        start_time = datetime.now()
        result = ExtractedText(
            filename=pdf_path.name,
            title=self._extract_title(pdf_path.name),
            extraction_time=start_time.isoformat()
        )

        try:
            if not pdf_path.exists():
                result.extraction_status = "failed"
                result.error_message = f"File not found: {pdf_path}"
                logger.error(result.error_message)
                return result

            with pdfplumber.open(pdf_path) as pdf:
                result.total_pages = len(pdf.pages)

                # Extract full text
                full_text = []
                page_to_chapter = {}

                for page_idx, page in enumerate(pdf.pages):
                    try:
                        text = page.extract_text() or ""
                        if text.strip():
                            full_text.append(text)
                    except Exception as e:
                        logger.warning(f"Error extracting page {page_idx+1} from {pdf_path.name}: {e}")
                        continue

                result.extracted_text = "\n".join(full_text)

                # Parse chapters and sections
                result.chapters = self._parse_chapters(result.extracted_text)

                # Extract metadata
                result.metadata = self._extract_metadata(pdf_path.name, result.extracted_text)

                # Update title based on metadata
                if result.metadata.get('title'):
                    result.title = result.metadata['title']

                # Merge known text metadata
                for known_text, meta in self.KNOWN_TEXTS.items():
                    if known_text.lower() in result.title.lower():
                        result.period = meta.get('period') or result.period
                        result.tradition = meta.get('tradition') or result.tradition
                        result.author = meta.get('author') or result.author
                        break

                # Calculate statistics
                result.char_count = len(result.extracted_text)
                result.verse_count = self._count_verses(result.extracted_text)

                # Truncate extremely long texts for manageability (keep original in extracted_text)
                if result.char_count > 1000000:
                    logger.info(f"Large text {result.filename}: {result.char_count} chars - storing full version")

                result.extraction_status = "success"
                logger.info(f"✅ Extracted {result.filename}: {result.total_pages} pages, {result.char_count} chars")

        except Exception as e:
            result.extraction_status = "failed"
            result.error_message = f"{type(e).__name__}: {str(e)}"
            logger.error(f"❌ Error processing {pdf_path.name}: {result.error_message}\n{traceback.format_exc()}")
            self.extraction_stats['errors'].append({
                'file': pdf_path.name,
                'error': result.error_message
            })

        finally:
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"Processing time for {pdf_path.name}: {elapsed:.2f}s")

        return result

    def _extract_title(self, filename: str) -> str:
        """
        Extract title from filename

        Handles various formats:
        - 2015.102832.Varahamihiras-Brihat-Samhitavoli-ii.pdf
        - मयमतम् Mayamatam Shailja pandey 1.pdf
        - Mayamatam.pdf
        """
        # Remove file extension
        name = filename.rsplit('.', 1)[0]

        # Remove ISBN-like prefixes (2015.123456.)
        name = re.sub(r'^\d{4}\.\d+\.', '', name)

        # Remove "Copy of" prefix
        name = re.sub(r'^Copy of\s+', '', name, flags=re.IGNORECASE)

        # Split on special separators and take meaningful part
        # Try to extract Sanskrit title first (before English)
        parts = re.split(r'\s(?=[A-Z]|\d)', name)
        if parts:
            name = parts[0]

        # Remove trailing version numbers like "vol 1", "2", etc.
        name = re.sub(r'\s+(?:vol|version|v|vol\.?)\s*\d+$', '', name, flags=re.IGNORECASE)

        # Clean up hyphens to spaces for readability
        name = name.replace('-', ' ')

        # Normalize whitespace
        name = ' '.join(name.split())

        return name.strip()

    def _extract_metadata(self, filename: str, text: str) -> Dict[str, Any]:
        """Extract metadata from filename and text"""
        metadata = {
            'filename': filename,
            'extracted_at': datetime.now().isoformat()
        }

        # Try to find author/translator from filename
        patterns = [
            r'(?:by|Pandey|Shukla|Sharma|pandey|sharma|shukla)',
            r'(\w+\s+\w+)(?:\.|$)'
        ]

        # Look for common metadata in first 500 chars
        first_chunk = text[:500]
        if 'author' in first_chunk.lower():
            metadata['has_author_section'] = True

        return metadata

    def _parse_chapters(self, text: str) -> List[Chapter]:
        """
        Parse chapter structure from extracted text

        Identifies chapters, sections, and verses
        """
        chapters = []
        lines = text.split('\n')

        current_chapter = None
        current_text = []
        current_page = 1
        verse_count = 0

        for line_idx, line in enumerate(lines):
            # Check for chapter markers
            chapter_match = None
            for pattern in self.CHAPTER_PATTERNS:
                match = re.match(pattern, line.strip())
                if match:
                    chapter_match = match
                    break

            if chapter_match:
                # Save previous chapter
                if current_chapter is not None:
                    current_chapter.text = '\n'.join(current_text).strip()
                    current_chapter.verse_count = verse_count
                    chapters.append(current_chapter)

                # Start new chapter
                try:
                    ch_num = int(chapter_match.group(1))
                    current_chapter = Chapter(
                        num=ch_num,
                        title=line.strip(),
                        text="",
                        page_start=current_page
                    )
                    current_text = []
                    verse_count = 0
                except (ValueError, IndexError):
                    current_chapter = None

            elif current_chapter is not None:
                # Check for verse markers
                for pattern in self.VERSE_PATTERNS:
                    if re.match(pattern, line.strip()):
                        verse_count += 1
                        break
                current_text.append(line)

            # Track page breaks (simple heuristic)
            if line.strip() == '' and len(current_text) > 50:
                current_page += 1

        # Save final chapter
        if current_chapter is not None:
            current_chapter.text = '\n'.join(current_text).strip()
            current_chapter.verse_count = verse_count
            current_chapter.page_end = current_page
            chapters.append(current_chapter)

        return chapters

    def _count_verses(self, text: str) -> int:
        """Count approximate number of verses in text"""
        count = 0
        for pattern in self.VERSE_PATTERNS:
            matches = re.findall(pattern, text, re.MULTILINE)
            count += len(matches)
        return count

    async def extract_all_pdfs(self, base_path: str) -> Tuple[List[ExtractedText], Dict[str, Any]]:
        """
        Extract from all PDFs in directory (async for speed)

        Args:
            base_path: Path to directory containing PDFs

        Returns:
            Tuple of (extracted_texts, statistics)
        """
        base_path = Path(base_path)

        if not base_path.exists():
            logger.error(f"Base path does not exist: {base_path}")
            return [], self.extraction_stats

        # Find all PDFs
        pdf_files = sorted(base_path.glob('*.pdf'))
        logger.info(f"Found {len(pdf_files)} PDF files to process")

        self.extraction_stats['total_files'] = len(pdf_files)

        # Process PDFs (using thread pool for I/O-bound operations)
        results = []
        loop = asyncio.get_event_loop()

        for idx, pdf_path in enumerate(pdf_files, 1):
            try:
                # Run in executor to avoid blocking event loop
                result = await loop.run_in_executor(
                    None,
                    self.extract_pdf,
                    pdf_path
                )
                results.append(result)

                if result.extraction_status == "success":
                    self.extraction_stats['successful'] += 1
                    self.extraction_stats['total_chars'] += result.char_count
                    self.extraction_stats['total_pages'] += result.total_pages
                else:
                    self.extraction_stats['failed'] += 1

                # Progress logging every 10 files
                if idx % 10 == 0:
                    logger.info(f"Progress: {idx}/{len(pdf_files)} files processed")

            except Exception as e:
                logger.error(f"Error queuing extraction for {pdf_path.name}: {e}")
                self.extraction_stats['failed'] += 1

        # Calculate statistics
        if self.extraction_stats['successful'] > 0:
            self.extraction_stats['avg_pages_per_text'] = (
                self.extraction_stats['total_pages'] / self.extraction_stats['successful']
            )

        self.extraction_stats['timestamp'] = datetime.now().isoformat()

        logger.info(f"""
        ✅ Extraction Complete
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        Total Files: {self.extraction_stats['total_files']}
        Successful: {self.extraction_stats['successful']}
        Failed: {self.extraction_stats['failed']}
        Total Characters: {self.extraction_stats['total_chars']:,}
        Total Pages: {self.extraction_stats['total_pages']:,}
        Avg Pages/Text: {self.extraction_stats['avg_pages_per_text']:.1f}
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """)

        return results, self.extraction_stats

    def save_manifest(
        self,
        results: List[ExtractedText],
        stats: Dict[str, Any],
        output_dir: Path
    ) -> Path:
        """
        Save extraction manifest and metadata

        Args:
            results: List of extracted texts
            stats: Extraction statistics
            output_dir: Directory to save manifest

        Returns:
            Path to manifest file
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        manifest = {
            'extraction_session': self.session_start,
            'completion_time': datetime.now().isoformat(),
            'statistics': stats,
            'texts': [r.to_dict() for r in results],
            'summary': {
                'total_texts': len(results),
                'success_rate': f"{(stats['successful']/stats['total_files']*100):.1f}%" if stats['total_files'] > 0 else "0%",
                'total_characters': stats['total_chars'],
                'total_pages': stats['total_pages'],
            }
        }

        manifest_path = output_dir / 'extracted_texts_manifest.json'
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ Manifest saved: {manifest_path}")
        return manifest_path

    def save_extracted_texts(
        self,
        results: List[ExtractedText],
        output_dir: Path
    ) -> Dict[str, Path]:
        """
        Save individual extracted texts to files

        Args:
            results: List of extracted texts
            output_dir: Directory to save texts

        Returns:
            Dict mapping filenames to output paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        saved_files = {}

        for result in results:
            if result.extraction_status == "success":
                # Create filename from title
                safe_filename = result.title.replace('/', '-').replace('\\', '-')
                safe_filename = f"{safe_filename}.txt"

                output_path = output_dir / safe_filename
                try:
                    with open(output_path, 'w', encoding='utf-8') as f:
                        # Write header
                        f.write(f"Title: {result.title}\n")
                        if result.author:
                            f.write(f"Author: {result.author}\n")
                        if result.period:
                            f.write(f"Period: {result.period}\n")
                        if result.tradition:
                            f.write(f"Tradition: {result.tradition}\n")
                        f.write(f"Pages: {result.total_pages}\n")
                        f.write(f"Verses: {result.verse_count}\n")
                        f.write("=" * 80 + "\n\n")

                        # Write extracted text
                        f.write(result.extracted_text)

                    saved_files[result.filename] = output_path
                    logger.info(f"✅ Saved: {output_path}")

                except Exception as e:
                    logger.error(f"Error saving {result.filename}: {e}")

        logger.info(f"✅ Saved {len(saved_files)} extracted texts")
        return saved_files


async def main():
    """
    Main extraction pipeline
    """
    extractor = VastuPDFExtractor()

    # Source directory
    source_dir = Path(
        "~/Library/CloudStorage/OneDrive-ALPHASENSETECHNOLOGY(INDIA)PRIVATELIMITED/Personal/Vastu shastra"
    ).expanduser()

    # Output directories
    output_base = Path("~/vastu_shastra_dss/data").expanduser()
    raw_texts_dir = output_base / "raw_texts"

    logger.info(f"Starting extraction from: {source_dir}")
    logger.info(f"Output directory: {raw_texts_dir}")

    # Extract all PDFs
    results, stats = await extractor.extract_all_pdfs(str(source_dir))

    # Save results
    manifest_path = extractor.save_manifest(results, stats, raw_texts_dir)
    saved_files = extractor.save_extracted_texts(results, raw_texts_dir)

    logger.info(f"\n✅ Extraction pipeline complete!")
    logger.info(f"Manifest: {manifest_path}")
    logger.info(f"Texts saved: {len(saved_files)} files")

    return results, stats


if __name__ == "__main__":
    # Run async extraction
    results, stats = asyncio.run(main())

    # Print summary
    print("\n" + "=" * 80)
    print("EXTRACTION SUMMARY")
    print("=" * 80)
    print(f"Total Files: {stats['total_files']}")
    print(f"Successful: {stats['successful']}")
    print(f"Failed: {stats['failed']}")
    print(f"Success Rate: {(stats['successful']/stats['total_files']*100):.1f}%" if stats['total_files'] > 0 else "0%")
    print(f"Total Characters: {stats['total_chars']:,}")
    print(f"Total Pages: {stats['total_pages']:,}")
    print(f"Average Pages/Text: {stats['avg_pages_per_text']:.1f}")
    print("=" * 80)
