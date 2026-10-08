# Vastu Shastra Text Processor - RAG Integration Guide

## Overview

The text processor provides semantic-aware chunking of Vastu Shastra texts, creating chunks optimized for retrieval-augmented generation (RAG) systems with Qdrant vector database.

## Chunk Output Format

Each chunk in `chunks.jsonl` contains:

```json
{
  "text": "The actual chunk text...",
  "source_file": "mayamatam.pdf",
  "chapter": "Chapter 3: Directional Principles",
  "section": "Orientation Guidelines",
  "verse_number": 45,
  "chunk_index": 0,
  "is_verse": true,
  "principle_type": "directional",
  "entities": ["north", "vastudosha", "kubera"],
  "sanskrit_terms": ["vastu", "kubera", "brahmasthana"],
  "char_count": 250,
  "token_estimate": 62,
  "confidence": 0.95
}
```

## RAG Integration Pipeline

### 1. Load and Validate Chunks

```python
from pathlib import Path
from vastu_shastra_dss.data_processing import load_chunks_from_jsonl

chunks = await load_chunks_from_jsonl(
    Path("data/chunks/chunks.jsonl")
)

print(f"Loaded {len(chunks)} chunks")
```

### 2. Embed Chunks for Qdrant

```python
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')

# Embed all chunk texts
embeddings = model.encode([chunk.text for chunk in chunks])

print(f"Generated {len(embeddings)} embeddings (dim: {embeddings[0].shape})")
```

### 3. Prepare Qdrant Points

```python
from qdrant_client.models import PointStruct

points = []
for idx, chunk in enumerate(chunks):
    point = PointStruct(
        id=idx,
        vector=embeddings[idx].tolist(),
        payload={
            # Text content
            'text': chunk.text,
            # Metadata
            'source_file': chunk.source_file,
            'chapter': chunk.chapter,
            'section': chunk.section,
            'verse_number': chunk.verse_number,
            'is_verse': chunk.is_verse,
            'principle_type': chunk.principle_type,
            # Searchable fields
            'entities': chunk.entities,
            'sanskrit_terms': chunk.sanskrit_terms,
            'char_count': chunk.char_count,
            'token_estimate': chunk.token_estimate,
            'confidence': chunk.confidence,
        }
    )
    points.append(point)

print(f"Prepared {len(points)} points for Qdrant")
```

### 4. Create Qdrant Collection

```python
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PayloadIndexInfo,
    PayloadSchemaType,
)

client = QdrantClient(url="http://localhost:6333")

# Create collection
collection_name = "vastu_texts_v1"

client.recreate_collection(
    collection_name=collection_name,
    vectors_config=VectorParams(
        size=768,  # paraphrase-multilingual-mpnet-base-v2 dimension
        distance=Distance.COSINE,
    ),
)

# Create payload indexes for filtered search
client.create_payload_index(
    collection_name=collection_name,
    field_name="principle_type",
    field_schema=PayloadSchemaType.KEYWORD,
)

client.create_payload_index(
    collection_name=collection_name,
    field_name="entities",
    field_schema=PayloadSchemaType.KEYWORD,
)

print(f"✅ Collection '{collection_name}' created")
```

### 5. Upsert Points to Qdrant

```python
client.upsert(
    collection_name=collection_name,
    points=points,
    wait=True,
)

print(f"✅ Uploaded {len(points)} points to Qdrant")
```

### 6. Query for Similar Chunks

```python
# Embed query
query_text = "How should the north direction be treated in Vastu?"
query_embedding = model.encode(query_text)

# Search Qdrant
results = client.search(
    collection_name=collection_name,
    query_vector=query_embedding,
    limit=5,
    score_threshold=0.7,
)

print(f"\n🔍 Top results for: '{query_text}'")
for i, result in enumerate(results, 1):
    payload = result.payload
    print(f"\n{i}. {payload['source_file']} - Score: {result.score:.2f}")
    print(f"   Chapter: {payload['chapter']}")
    print(f"   Type: {payload['principle_type']}")
    print(f"   Entities: {', '.join(payload['entities'][:3])}")
    print(f"   Text: {payload['text'][:150]}...")
```

### 7. Filtered Search with Knowledge Graph

```python
# Search with filters for specific principle types
results = client.search(
    collection_name=collection_name,
    query_vector=query_embedding,
    query_filter={
        "must": [
            {
                "key": "principle_type",
                "match": {
                    "value": "directional"
                }
            }
        ]
    },
    limit=5,
)

print(f"Found {len(results)} directional principles")
```

## Chunking Strategy Details

### Target Sizes

- **Target**: 1000-1500 chars (120-200 tokens)
- **Maximum**: 2000 chars (500 tokens)
- **Minimum**: 500 chars (125 tokens)
- **Overlap**: 100 chars for context preservation

### Semantic Boundaries (Priority Order)

1. **Verse markers** (Sloka 45, verse 12, doha 3)
2. **Paragraph breaks** (double newlines)
3. **Sanskrit terminators** (॥, |, iti)
4. **Sentence boundaries** (`. ` + capital letter)
5. **Clause/phrase boundaries** (semicolons, commas)

### Metadata Extraction

**Principle Types:**
- `directional` - Spatial orientation and direction-based principles
- `remedial` - Corrections and remedies for Vastu defects
- `construction` - Building design and structural guidelines
- `temporal` - Timing, seasons, and auspicious moments

**Entities Detected:**
- Directions: north, northeast, east, southeast, south, southwest, west, northwest
- Doshas: vastudosha, pitta, vata, kapha
- Remedies: vastu, remedy, shaanti, yantra, mudra, mantra
- Materials: marble, granite, wood, copper, clay, brick

**Sanskrit Terms:**
- Capitalized proper nouns and technical terms
- Transliterated Sanskrit words
- Devanagari script markers

## Quality Assurance

The QA report includes:

```
📊 Overall Statistics:
   Total Chunks: ~50,000
   Average Chunk Size: 1,200 chars (300 tokens)
   Coverage: 100% of source texts

⚠️ Quality Checks:
   Duplicate Chunks: 0
   Fragments < 500 chars: <1%

📈 Size Distribution:
   1000-1500 chars: 65%
   1500-2000 chars: 25%
   <1000 chars: 10%

🎯 Principle Type Distribution:
   Directional: 40%
   Remedial: 35%
   Construction: 20%
   Temporal: 5%
```

## Performance Tuning

### For Large-Scale Processing

1. **Batch Processing**
   ```python
   batch_size = 100
   for i in range(0, len(extracted_texts), batch_size):
       batch = extracted_texts[i:i+batch_size]
       chunks = await chunk_vastu_texts(batch)
       await save_chunks_to_jsonl(chunks, output_path)
   ```

2. **Parallel Embedding**
   ```python
   embeddings = model.encode(
       [chunk.text for chunk in chunks],
       batch_size=32,
       show_progress_bar=True,
   )
   ```

3. **Memory-Efficient Upserting**
   ```python
   batch_size = 1000
   for i in range(0, len(points), batch_size):
       client.upsert(
           collection_name=collection_name,
           points=points[i:i+batch_size],
           wait=True,
       )
   ```

## Integration with FastAPI Backend

```python
from fastapi import FastAPI
from vastu_shastra_dss.data_processing import load_chunks_from_jsonl

app = FastAPI()

# Load chunks on startup
chunks = None

@app.on_event("startup")
async def load_chunks():
    global chunks
    chunks = await load_chunks_from_jsonl(
        Path("data/chunks/chunks.jsonl")
    )
    print(f"✅ Loaded {len(chunks)} chunks")

@app.get("/search")
async def search(query: str, principle_type: str = None, limit: int = 5):
    """Search Qdrant for relevant chunks"""
    # Embed query
    query_embedding = model.encode(query)
    
    # Build filter if principle_type specified
    query_filter = None
    if principle_type:
        query_filter = {
            "must": [
                {
                    "key": "principle_type",
                    "match": {"value": principle_type}
                }
            ]
        }
    
    # Search
    results = qdrant_client.search(
        collection_name="vastu_texts_v1",
        query_vector=query_embedding,
        query_filter=query_filter,
        limit=limit,
    )
    
    return {
        "query": query,
        "results": [
            {
                "score": r.score,
                "source": r.payload["source_file"],
                "chapter": r.payload["chapter"],
                "principle_type": r.payload["principle_type"],
                "text": r.payload["text"],
            }
            for r in results
        ]
    }
```

## Troubleshooting

### Low Chunk Sizes?
- Verify source texts are being extracted correctly
- Check that verse boundary detection patterns match your texts
- Increase `target_size` parameter in `chunk_vastu_texts()`

### High Duplication?
- Check for preprocessing issues in text extraction
- Verify chunk overlap settings
- Consider text normalization (whitespace, punctuation)

### Poor Search Results?
- Verify embeddings are being generated correctly
- Check Qdrant payload indexes are created
- Test with simpler queries first
- Inspect top-k results for principle_type matching

### Memory Issues?
- Use batch processing for large document sets
- Reduce batch size for embedding/upserting
- Consider streaming chunks from JSONL instead of loading all

## References

- Qdrant Python Client: https://github.com/qdrant/qdrant-client
- Sentence Transformers: https://www.sbert.net/
- Vastu Shastra Knowledge Graph: `data/kg/` directory
