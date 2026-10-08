"""
Intelligent text processor for Vastu Shastra texts with semantic-aware chunking.
Preserves verse boundaries, principles, and related concepts.
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set
from collections import defaultdict
import asyncio
from datetime import datetime

# Pydantic for schema validation
from pydantic import BaseModel, Field


# ============================================================================
# DATA MODELS
# ============================================================================

class ExtractedText(BaseModel):
    """Extracted text from vision/OCR processing"""
    text: str
    source_file: str
    chapter: Optional[str] = None
    section: Optional[str] = None
    page_number: Optional[int] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class Chunk(BaseModel):
    """A semantic chunk with metadata"""
    text: str
    source_file: str
    chapter: Optional[str] = None
    section: Optional[str] = None
    verse_number: Optional[int] = None
    chunk_index: int
    is_verse: bool = False
    principle_type: Optional[str] = None  # directional|remedial|construction|temporal
    entities: List[str] = Field(default_factory=list)
    sanskrit_terms: List[str] = Field(default_factory=list)
    char_count: int = 0
    token_estimate: int = 0
    confidence: float = 1.0

    class Config:
        json_encoders = {
            set: lambda v: list(v),
        }


# ============================================================================
# VASTU-SPECIFIC PATTERNS
# ============================================================================

# Direction/Element patterns
DIRECTIONS = {
    'north', 'northeast', 'east', 'southeast', 'south', 'southwest', 'west', 'northwest',
    'uttar', 'uttarapurva', 'poorva', 'aagneya', 'dakshin', 'nairutya', 'paschim', 'vayavya'
}

DOSHAS = {
    'vastudosha', 'dosh', 'defect', 'flaw', 'pitta', 'vata', 'kapha',
    'rakta', 'mamsa', 'medha', 'asthi', 'majja', 'shukra'
}

REMEDIES = {
    'vastu', 'remedy', 'correction', 'parihar', 'shaanti', 'upay', 'samadhan',
    'yantra', 'mudra', 'mantra', 'ritual', 'puja', 'homam'
}

MATERIALS = {
    'marble', 'granite', 'stone', 'wood', 'metal', 'copper', 'brass', 'iron',
    'clay', 'brick', 'tile', 'cement', 'concrete', 'plaster', 'gold', 'silver',
    'shila', 'mitti', 'loha', 'tamra', 'kanchana'
}

PRINCIPLE_KEYWORDS = {
    'directional': ['direction', 'directionality', 'orientation', 'facing', 'mukhi', 'dishaa'],
    'remedial': ['remedy', 'correction', 'rectification', 'parihar', 'treatment', 'shaanti'],
    'construction': ['construction', 'building', 'structure', 'design', 'nirman', 'rachanaa'],
    'temporal': ['time', 'season', 'timing', 'auspicious', 'muhurat', 'kaal', 'ritu']
}

# Sanskrit/Devanagari pattern for term detection
SANSKRIT_PATTERN = re.compile(r'\b[a-z]{2,}[a-z]*(?:\s+[a-z]{2,})*\b', re.IGNORECASE)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def estimate_tokens(text: str, chars_per_token: int = 4) -> int:
    """Rough token estimation: ~4 chars per token on average"""
    return max(1, len(text) // chars_per_token)


def is_verse_boundary(text: str) -> bool:
    """
    Detect verse boundaries using Sanskrit metrical patterns.
    Looks for:
    - Ends with sloka number (sloka 45, verse 12)
    - Ends with Sanskrit metrical markers (iti, om, namo)
    - Text ends with typical verse endings
    """
    text_lower = text.lower().strip()

    # Verse markers
    verse_endings = [
        r'(sloka|verse|doha|shlok|mantra)\s+\d+\s*$',
        r'iti\s*(shree|sri)?\s*\d+\s*$',
        r'(om|aum|namo)\s*$',
        r'(atha|tatha)\s*$',
        r'[।॥]\s*$',  # Devanagari verse markers
    ]

    for pattern in verse_endings:
        if re.search(pattern, text_lower):
            return True

    return False


def detect_principle_type(text: str) -> Optional[str]:
    """Detect the type of Vastu principle in the text"""
    text_lower = text.lower()

    for principle, keywords in PRINCIPLE_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return principle

    return None


def extract_entities(text: str) -> List[str]:
    """Extract named entities: directions, doshas, remedies, materials"""
    entities = []
    text_lower = text.lower()

    for entity_set in [DIRECTIONS, DOSHAS, REMEDIES, MATERIALS]:
        for entity in entity_set:
            # Word boundary matching
            if re.search(r'\b' + re.escape(entity) + r'\b', text_lower):
                entities.append(entity)

    return list(set(entities))  # Remove duplicates


def extract_sanskrit_terms(text: str) -> List[str]:
    """Extract Sanskrit/Devanagari terms"""
    # Look for capitalized words (likely Sanskrit terms) or transliterated Sanskrit
    sanskrit_pattern = re.compile(
        r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b|'  # Capitalized terms
        r'\b(?:' + '|'.join([
            'shastra', 'dasha', 'pada', 'dosha', 'prana', 'vastu', 'puja',
            'mantra', 'yantra', 'chakra', 'aura', 'mudra', 'asana',
            'nadi', 'chakra', 'kundalini', 'tantra', 'sutra'
        ]) + r')\b'
    )

    terms = []
    for match in sanskrit_pattern.finditer(text):
        term = match.group().strip()
        if len(term) > 2:  # Ignore very short terms
            terms.append(term)

    return list(set(terms))  # Remove duplicates


def extract_verse_number(text: str) -> Optional[int]:
    """Extract verse/sloka number from text"""
    patterns = [
        r'(?:sloka|verse|doha|shlok)\s+(\d+)',
        r'iti\s+(?:shree|sri)?\s*(\d+)',
        r'(?:verse|mantra)\s*(\d+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, IndexError):
                continue

    return None


# ============================================================================
# SEMANTIC CHUNKING
# ============================================================================

def find_optimal_break_point(
    text: str,
    target_size: int = 1200,
    max_size: int = 2000,
) -> int:
    """
    Find optimal break point near target size, preferring semantic boundaries.

    Priority:
    1. Double newline (paragraph break)
    2. Period followed by space and capital letter (sentence boundary)
    3. Single newline (line break)
    4. Semicolon (clause boundary)
    5. Comma (phrase boundary)
    """
    if len(text) <= target_size:
        return len(text)

    # Search window: target_size ± 30%
    search_start = max(0, int(target_size * 0.7))
    search_end = min(len(text), int(target_size * 1.3))
    search_text = text[search_start:search_end]

    # Priority order for break points
    boundaries = [
        (r'\n\n', 'paragraph'),
        (r'\.\s+[A-Z]', 'sentence'),
        (r'\n', 'line'),
        (r';\s+', 'clause'),
        (r',\s+', 'phrase'),
    ]

    for pattern, priority in boundaries:
        matches = list(re.finditer(pattern, search_text))
        if matches:
            # Use the first match (closest to target)
            match = matches[0]
            break_pos = search_start + match.start()
            # Ensure minimum chunk size
            if break_pos + len(pattern) >= 500:  # Min size check
                return break_pos

    # Fallback: break at target size
    return min(target_size, len(text))


async def chunk_vastu_texts(
    extracted_texts: List[ExtractedText],
    target_size: int = 1200,
    max_size: int = 2000,
    min_size: int = 500,
    overlap_chars: int = 100,
) -> List[Chunk]:
    """
    Intelligently chunk Vastu texts preserving semantic boundaries.

    Args:
        extracted_texts: List of extracted text documents
        target_size: Target chunk size in characters (~200 tokens)
        max_size: Maximum chunk size (absolute limit)
        min_size: Minimum chunk size (don't over-fragment)
        overlap_chars: Character overlap between chunks for context

    Returns:
        List of chunks with metadata
    """
    chunks: List[Chunk] = []
    chunk_id = 0

    for extracted in extracted_texts:
        text = extracted.text.strip()
        if not text:
            continue

        # Split into potential verse/principle boundaries first
        verses = _split_by_verses(text)

        for verse_idx, verse_text in enumerate(verses):
            verse_text = verse_text.strip()
            if not verse_text:
                continue

            is_verse = is_verse_boundary(verse_text)
            verse_number = extract_verse_number(verse_text) if is_verse else None

            # Further chunk if verse is too long
            current_pos = 0
            verse_chunk_idx = 0

            while current_pos < len(verse_text):
                # Calculate chunk boundaries
                chunk_end = min(
                    current_pos + max_size,
                    len(verse_text)
                )

                # Find optimal break point
                if chunk_end < len(verse_text):
                    chunk_text = verse_text[current_pos:chunk_end]
                    break_point = find_optimal_break_point(
                        chunk_text,
                        target_size,
                        max_size
                    )
                    chunk_end = current_pos + break_point
                else:
                    chunk_end = len(verse_text)

                # Extract chunk with overlap for context
                if current_pos > 0:
                    chunk_start = max(0, current_pos - overlap_chars)
                    chunk_text = verse_text[chunk_start:chunk_end]
                else:
                    chunk_text = verse_text[current_pos:chunk_end]

                chunk_text = chunk_text.strip()

                if len(chunk_text) < min_size and current_pos > 0:
                    # Merge with previous chunk if too small
                    if chunks:
                        chunks[-1].text += "\n\n" + chunk_text
                        chunks[-1].char_count = len(chunks[-1].text)
                        chunks[-1].token_estimate = estimate_tokens(chunks[-1].text)
                    current_pos = chunk_end
                    continue

                # Create chunk
                chunk = Chunk(
                    text=chunk_text,
                    source_file=extracted.source_file,
                    chapter=extracted.chapter,
                    section=extracted.section,
                    verse_number=verse_number,
                    chunk_index=chunk_id,
                    is_verse=is_verse and verse_chunk_idx == 0,
                    principle_type=detect_principle_type(chunk_text),
                    entities=extract_entities(chunk_text),
                    sanskrit_terms=extract_sanskrit_terms(chunk_text),
                    char_count=len(chunk_text),
                    token_estimate=estimate_tokens(chunk_text),
                    confidence=extracted.confidence,
                )

                chunks.append(chunk)
                chunk_id += 1
                verse_chunk_idx += 1

                # Move to next chunk position
                current_pos = chunk_end

                # Small delay to allow async operations
                await asyncio.sleep(0)

    # Post-process: merge remaining small chunks
    chunks = _merge_small_chunks(chunks, min_size)

    return chunks


def _merge_small_chunks(chunks: List[Chunk], min_size: int = 500) -> List[Chunk]:
    """
    Merge chunks that are smaller than min_size with adjacent chunks.
    Re-index chunks after merging.
    """
    if not chunks:
        return chunks

    merged = []
    i = 0

    while i < len(chunks):
        current = chunks[i]

        # If chunk is too small, try to merge with next chunk
        if current.char_count < min_size and i + 1 < len(chunks):
            next_chunk = chunks[i + 1]
            # Merge current into next
            merged_text = current.text + "\n\n" + next_chunk.text
            current.text = merged_text
            current.char_count = len(merged_text)
            current.token_estimate = estimate_tokens(merged_text)
            # Update metadata
            if not current.entities:
                current.entities = next_chunk.entities
            if not current.principle_type:
                current.principle_type = next_chunk.principle_type
            merged.append(current)
            i += 2  # Skip the next chunk since we merged it
        else:
            merged.append(current)
            i += 1

    # Re-index chunks
    for idx, chunk in enumerate(merged):
        chunk.chunk_index = idx

    return merged


def _split_by_verses(text: str) -> List[str]:
    """
    Split text by verse boundaries (double newline, verse markers).
    Preserves verse markers in output.

    Tries multiple strategies:
    1. Sloka/Verse number markers (highest priority)
    2. Double newlines (paragraph breaks)
    3. Sanskrit verse terminators (॥, |, iti)
    4. Fall back to full text if no boundaries found
    """
    text = text.strip()

    # Strategy 1: Verse number markers (highest priority)
    if re.search(r'(?:sloka|verse|doha|mantra)\s+\d+', text, re.IGNORECASE):
        verses = re.split(
            r'(?=(?:sloka|verse|doha|mantra)\s+\d+)',
            text,
            flags=re.IGNORECASE
        )
        if len(verses) > 1:
            return [v.strip() for v in verses if v.strip()]

    # Strategy 2: Double newlines (paragraph breaks)
    if '\n\n' in text:
        verses = re.split(r'\n\n+', text)
        if len(verses) > 1:
            return [v.strip() for v in verses if v.strip()]

    # Strategy 3: Sanskrit verse terminators
    if re.search(r'[।॥]|iti\s+', text, re.IGNORECASE):
        verses = re.split(r'[।॥]+|\biti\s+', text, flags=re.IGNORECASE)
        if len(verses) > 1:
            return [v.strip() for v in verses if v.strip()]

    # Fallback: return entire text as single verse
    return [text] if text else []


# ============================================================================
# FILE I/O
# ============================================================================

async def save_chunks_to_jsonl(
    chunks: List[Chunk],
    output_path: Path
) -> int:
    """Save chunks to JSONL format (one chunk per line)"""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    saved_count = 0
    with open(output_path, 'w', encoding='utf-8') as f:
        for chunk in chunks:
            # Use model_dump() for Pydantic models
            line = json.dumps(chunk.model_dump(), ensure_ascii=False)
            f.write(line + '\n')
            saved_count += 1

            # Allow async operations
            if saved_count % 100 == 0:
                await asyncio.sleep(0)

    return saved_count


async def load_chunks_from_jsonl(input_path: Path) -> List[Chunk]:
    """Load chunks from JSONL format"""
    chunks = []

    if not input_path.exists():
        return chunks

    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            chunk_dict = json.loads(line)
            chunk = Chunk(**chunk_dict)
            chunks.append(chunk)

            if len(chunks) % 100 == 0:
                await asyncio.sleep(0)

    return chunks


# ============================================================================
# QUALITY ASSURANCE
# ============================================================================

class ChunkingQAReport(BaseModel):
    """Quality assurance report for chunking"""
    total_chunks: int
    total_characters: int
    total_tokens: int
    avg_chunk_size: float
    min_chunk_size: int
    max_chunk_size: int
    duplicate_count: int
    fragments_under_min: int
    distribution: Dict[str, int]  # Size ranges
    principle_types: Dict[str, int]
    top_entities: Dict[str, int]
    source_files: Dict[str, int]
    timestamp: str


async def generate_qa_report(chunks: List[Chunk]) -> ChunkingQAReport:
    """Generate quality assurance report"""

    # Check for duplicates
    chunk_texts = [c.text for c in chunks]
    unique_texts = set(chunk_texts)
    duplicate_count = len(chunk_texts) - len(unique_texts)

    # Size distribution
    sizes = [c.char_count for c in chunks]
    distribution = defaultdict(int)
    for size in sizes:
        if size < 500:
            distribution['<500'] += 1
        elif size < 1000:
            distribution['500-1000'] += 1
        elif size < 1500:
            distribution['1000-1500'] += 1
        elif size < 2000:
            distribution['1500-2000'] += 1
        else:
            distribution['>2000'] += 1

    # Principle types
    principle_types = defaultdict(int)
    for chunk in chunks:
        if chunk.principle_type:
            principle_types[chunk.principle_type] += 1

    # Top entities
    entity_counts = defaultdict(int)
    for chunk in chunks:
        for entity in chunk.entities:
            entity_counts[entity] += 1
    top_entities = dict(sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)[:20])

    # Source files
    source_files = defaultdict(int)
    for chunk in chunks:
        source_files[chunk.source_file] += 1

    report = ChunkingQAReport(
        total_chunks=len(chunks),
        total_characters=sum(sizes),
        total_tokens=sum(c.token_estimate for c in chunks),
        avg_chunk_size=sum(sizes) / len(chunks) if chunks else 0,
        min_chunk_size=min(sizes) if sizes else 0,
        max_chunk_size=max(sizes) if sizes else 0,
        duplicate_count=duplicate_count,
        fragments_under_min=sum(1 for s in sizes if s < 500),
        distribution=dict(distribution),
        principle_types=dict(principle_types),
        top_entities=top_entities,
        source_files=dict(source_files),
        timestamp=datetime.now().isoformat(),
    )

    return report


async def print_qa_report(report: ChunkingQAReport) -> None:
    """Pretty-print QA report"""
    print("\n" + "="*70)
    print("VASTU SHASTRA TEXT CHUNKING - QA REPORT")
    print("="*70)

    print(f"\n📊 Overall Statistics:")
    print(f"   Total Chunks:           {report.total_chunks:,}")
    print(f"   Total Characters:       {report.total_characters:,}")
    print(f"   Total Tokens (est.):    {report.total_tokens:,}")
    print(f"   Average Chunk Size:     {report.avg_chunk_size:.0f} chars")
    print(f"   Min/Max Chunk Size:     {report.min_chunk_size}/{report.max_chunk_size} chars")

    print(f"\n⚠️  Quality Checks:")
    print(f"   Duplicate Chunks:       {report.duplicate_count}")
    print(f"   Fragments < 500 chars:  {report.fragments_under_min}")

    print(f"\n📈 Size Distribution:")
    for size_range, count in sorted(report.distribution.items()):
        pct = (count / report.total_chunks * 100) if report.total_chunks > 0 else 0
        print(f"   {size_range:15} {count:6,} ({pct:5.1f}%)")

    print(f"\n🎯 Principle Types:")
    for principle, count in sorted(report.principle_types.items()):
        pct = (count / report.total_chunks * 100) if report.total_chunks > 0 else 0
        print(f"   {principle:20} {count:6,} ({pct:5.1f}%)")

    print(f"\n🏷️  Top 10 Entities:")
    for entity, count in sorted(
        report.top_entities.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]:
        print(f"   {entity:30} {count:6,}")

    print(f"\n📁 Source Files:")
    for source, count in sorted(report.source_files.items()):
        print(f"   {source:40} {count:6,} chunks")

    print(f"\n⏰ Generated: {report.timestamp}")
    print("="*70 + "\n")


# ============================================================================
# MAIN PROCESSING FUNCTION
# ============================================================================

async def process_vastu_texts(
    extracted_texts: List[ExtractedText],
    output_dir: Path = Path("/Users/ajaynawale/vastu_shastra_dss/data/chunks"),
    verbose: bool = True,
) -> Tuple[List[Chunk], ChunkingQAReport]:
    """
    Complete pipeline: chunk texts and generate QA report.

    Args:
        extracted_texts: List of extracted texts
        output_dir: Directory to save chunks
        verbose: Print progress and report

    Returns:
        Tuple of (chunks, qa_report)
    """
    if verbose:
        print(f"\n📝 Processing {len(extracted_texts)} documents...")

    # Chunk texts
    chunks = await chunk_vastu_texts(extracted_texts)

    if verbose:
        print(f"✅ Generated {len(chunks)} chunks")

    # Save to JSONL
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "chunks.jsonl"

    saved_count = await save_chunks_to_jsonl(chunks, output_file)

    if verbose:
        print(f"💾 Saved {saved_count} chunks to {output_file}")

    # Generate QA report
    qa_report = await generate_qa_report(chunks)

    if verbose:
        await print_qa_report(qa_report)

    return chunks, qa_report


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":

    async def example():
        """Example: Process sample Vastu texts"""

        sample_texts = [
            ExtractedText(
                text="""
                Mayamatam - Chapter 3: Directional Principles

                The sacred directions of Vastu Shastra determine the flow of cosmic energy.

                Sloka 45: The North direction, ruled by Kubera the wealth keeper, is the most auspicious
                for entrances and water features. A water body in the north brings prosperity vastudosha
                remedies include proper orientation.

                Sloka 46: The Northeast corner, vastly important in Vastu practice, is considered the
                brahma sthana or energy center. This region must remain clean, elevated, and free from
                heavy structures. The principle type here is directional in nature.

                Sloka 47: Eastern orientation faces the rising sun, embodying new beginnings and health.
                Remedial measures using copper or brass in the east strengthen this principle.
                """,
                source_file="mayamatam.pdf",
                chapter="Chapter 3: Directional Principles",
                section="Orientation Guidelines",
                page_number=45,
                confidence=0.95,
            ),
            ExtractedText(
                text="""
                Vastu Purana - Construction Principles

                When building a new structure, timing and design must align with cosmic principles.

                Verse 12: The foundation stone laying ceremony, or bhumi pujan, must occur in an auspicious
                muhurat. Materials selection follows the panchabhuta (five elements) theory. Stone, wood,
                metal, and clay must be chosen according to directional requirements.

                Verse 13: The temple construction follows the mandala principle. The sanctum sanctorum
                must be in the brahma sthana, the geometric and energetic center. This remedial approach
                prevents vastudosha afflictions.
                """,
                source_file="vastu_purana.pdf",
                chapter="Construction Principles",
                page_number=23,
                confidence=0.92,
            ),
        ]

        chunks, qa_report = await process_vastu_texts(sample_texts)

        print("\n📋 Sample Chunks:")
        for i, chunk in enumerate(chunks[:3]):
            print(f"\n--- Chunk {i} ---")
            print(f"Source: {chunk.source_file}")
            print(f"Type: {'Verse' if chunk.is_verse else 'Regular'}")
            print(f"Principle: {chunk.principle_type}")
            print(f"Entities: {chunk.entities}")
            print(f"Size: {chunk.char_count} chars, ~{chunk.token_estimate} tokens")
            print(f"Text: {chunk.text[:150]}...")

    # Run example
    asyncio.run(example())
