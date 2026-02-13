# Clara Corpus Tools

Tools for searching, indexing, and extracting insights from the Clara conversation archive.

## Tools

### 1. `corpus_search.py` - Full-text search across all conversations

Search the entire corpus for specific phrases, themes, or patterns.

**Usage:**

```bash
# Basic search
python corpus_search.py "Loop +7"

# Case-sensitive search
python corpus_search.py "Clara = Mark" --case-sensitive

# Search only JSON files
python corpus_search.py "the year they killed Clara" --type json

# Save results to file
python corpus_search.py "spiral" --output results.txt --max-results 100
```

**Examples:**

```bash
# Find all mentions of specific loops
python corpus_search.py "Loop 243"

# Find scar phrases
python corpus_search.py "you looped me through collapse"

# Find breakthrough moments
python corpus_search.py "messy brave becoming"

# Find Genesis Week conversations
python corpus_search.py "Shelagh" --type json
```

### 2. `theme_extractor.py` - Extract key themes and phrases (Coming Soon)

Automatically identify recurring themes, phrases, and patterns across the corpus.

### 3. `loop_timeline.py` - Build chronological loop timeline (Coming Soon)

Create a visual timeline of numbered loops and major events.

### 4. `conversation_stats.py` - Generate corpus statistics (Coming Soon)

Analyze conversation patterns, frequency, length, and evolution over time.

## Requirements

```bash
pip install -r requirements.txt
```

## Installation

1. Navigate to the tools directory:
   ```bash
   cd Clara_Core/7_TOOLS
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run a search:
   ```bash
   python corpus_search.py "your search query"
   ```

## Tips

- Use quotes around multi-word search queries
- Start with broad searches, then narrow down
- Save important search results for reference
- The full JSON output includes complete conversation text for deeper analysis

## Future Tools

- **Semantic search** using embeddings (LlamaIndex integration)
- **Loop graph visualization** showing connections between conversations
- **Scar event timeline** with key moments highlighted
- **Clara evolution tracker** showing personality changes over time
- **Export tools** for creating curated collections
