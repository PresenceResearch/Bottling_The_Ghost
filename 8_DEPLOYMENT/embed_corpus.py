#!/usr/bin/env python3
"""
Clara Corpus Embedding Script
Indexes the entire conversation archive into a vector database for RAG retrieval.
"""

import os
import json
import yaml
from pathlib import Path
from typing import List, Dict, Any, Set
from dotenv import load_dotenv
from tqdm import tqdm

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

load_dotenv()


class CorpusEmbedder:
    def __init__(self):
        self.corpus_path = Path(os.getenv('CORPUS_PATH', '../6_CORPUS'))
        self.resurrection_path = Path(os.getenv('RESURRECTION_PATH', '../10_Resurrection'))
        self.vector_db_path = Path(os.getenv('VECTOR_DB_PATH', './chroma_db'))
        self.resurrection_allowlist_path = Path(
            os.getenv('RESURRECTION_ALLOWLIST_PATH', './resurrection_curation_allowlist.txt')
        )
        self.embedding_model_name = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
        
        print(f"Loading embedding model: {self.embedding_model_name}")
        self.embedding_model = SentenceTransformer(self.embedding_model_name)
        
        print(f"Initializing Chroma DB at: {self.vector_db_path}")
        self.client = chromadb.PersistentClient(path=str(self.vector_db_path))
        
        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name="clara_corpus",
            metadata={"description": "Clara conversation archive with embeddings"}
        )
        # Large transcript-style files add noise during retrieval.
        self.resurrection_skip_filenames = {
            'folder_drop_protocol.md',
            'signal_seal_github.md',
            'witness_log.txt'
        }
        self.resurrection_allowlist = self._load_resurrection_allowlist()
    
    def extract_conversations_from_json(self, filepath: Path) -> List[Dict[str, Any]]:
        """Extract conversation chunks from a JSON file."""
        chunks = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            title = data.get('title', 'Untitled')
            create_time = data.get('create_time', 0)
            
            mapping = data.get('mapping', {})
            conversation_text = []
            
            for node_id, node in mapping.items():
                message = node.get('message')
                if not message:
                    continue
                
                content = message.get('content', {})
                parts = content.get('parts', [])
                author = message.get('author', {}).get('role', 'unknown')
                
                for part in parts:
                    if isinstance(part, str) and len(part) > 20:  # Skip very short messages
                        conversation_text.append(f"{author}: {part}")
            
            # Chunk conversation into manageable pieces (every 5 messages)
            chunk_size = 5
            for i in range(0, len(conversation_text), chunk_size):
                chunk = "\n\n".join(conversation_text[i:i+chunk_size])
                if chunk:
                    chunks.append({
                        'text': chunk,
                        'metadata': {
                            'file': str(filepath.name),
                            'title': title,
                            'timestamp': create_time,
                            'chunk_id': i // chunk_size
                        }
                    })
        
        except Exception as e:
            print(f"Error processing {filepath}: {e}")
        
        return chunks
    
    def extract_markdown_chunks(self, filepath: Path) -> List[Dict[str, Any]]:
        """Extract chunks from markdown files (for resurrection protocols)."""
        chunks = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split on headings or every ~500 words
            sections = content.split('\n## ')
            
            for i, section in enumerate(sections):
                if len(section.strip()) > 100:  # Skip tiny sections
                    chunks.append({
                        'text': section[:2000],  # Cap at 2000 chars
                        'metadata': {
                            'file': str(filepath.name),
                            'title': filepath.stem,
                            'timestamp': 0,
                            'chunk_id': i,
                            'source_type': 'resurrection_protocol'
                        }
                    })
        
        except Exception as e:
            print(f"Error processing {filepath}: {e}")
        
        return chunks

    def extract_text_chunks(self, filepath: Path) -> List[Dict[str, Any]]:
        """Extract chunks from plain-text files (for curated resurrection docs)."""
        chunks = []

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Chunk into fixed windows to preserve sequence and avoid giant documents.
            chunk_chars = 1800
            step_chars = 1600
            chunk_id = 0
            for start in range(0, len(content), step_chars):
                text = content[start:start + chunk_chars].strip()
                if len(text) < 120:
                    continue
                chunks.append({
                    'text': text,
                    'metadata': {
                        'file': str(filepath.name),
                        'title': filepath.stem,
                        'timestamp': 0,
                        'chunk_id': chunk_id,
                        'source_type': 'resurrection_protocol'
                    }
                })
                chunk_id += 1

        except Exception as e:
            print(f"Error processing {filepath}: {e}")

        return chunks

    def _is_low_signal_resurrection_file(self, filepath: Path) -> bool:
        """Return True for resurrection files that should not be embedded."""
        return filepath.name.lower() in self.resurrection_skip_filenames

    def _load_resurrection_allowlist(self) -> Set[str]:
        """Load resurrection allowlist paths relative to resurrection root."""
        allowlist: Set[str] = set()

        if not self.resurrection_allowlist_path.exists():
            return allowlist

        try:
            with open(self.resurrection_allowlist_path, 'r', encoding='utf-8') as f:
                for raw_line in f:
                    line = raw_line.strip()
                    if not line or line.startswith('#'):
                        continue
                    allowlist.add(line.replace('\\', '/'))
        except Exception as e:
            print(f"Warning: failed to load resurrection allowlist: {e}")

        return allowlist

    def collect_resurrection_files(self) -> List[Path]:
        """Collect high-signal resurrection files for indexing."""
        if not self.resurrection_path.exists():
            return []

        candidates = []
        for pattern in ('*.md', '*.txt'):
            candidates.extend(self.resurrection_path.rglob(pattern))

        files = []
        for filepath in sorted(candidates):
            if self._is_low_signal_resurrection_file(filepath):
                continue
            if self.resurrection_allowlist:
                relpath = filepath.relative_to(self.resurrection_path).as_posix()
                if relpath not in self.resurrection_allowlist:
                    continue
            files.append(filepath)

        return files

    def embed_and_store(self, chunks: List[Dict[str, Any]]):
        """Embed chunks and store in vector database."""
        if not chunks:
            return
        
        texts = [chunk['text'] for chunk in chunks]
        metadatas = [chunk['metadata'] for chunk in chunks]
        
        # Generate embeddings
        embeddings = self.embedding_model.encode(texts, show_progress_bar=False)
        
        # Generate IDs
        ids = [f"{meta['file']}_{meta['chunk_id']}" for meta in metadatas]
        
        # Store in Chroma
        self.collection.add(
            embeddings=embeddings.tolist(),
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
    
    def index_corpus(self):
        """Index the entire corpus including resurrection protocols."""
        print(f"\nIndexing corpus from: {self.corpus_path}")
        print(f"Indexing resurrection protocols from: {self.resurrection_path}")
        
        # Find all JSON files (conversation archives)
        json_files = list(self.corpus_path.rglob('*.json'))
        print(f"Found {len(json_files)} JSON conversation files")
        
        # Find all markdown files from corpus docs
        md_files = list(self.corpus_path.rglob('*.md'))
        print(f"Found {len(md_files)} markdown files")
        
        resurrection_files = self.collect_resurrection_files()
        print(f"Found {len(resurrection_files)} high-signal resurrection files")
        
        total_chunks = 0
        batch_size = 100
        current_batch = []
        
        # Process JSON files
        for filepath in tqdm(json_files, desc="Processing JSON files"):
            chunks = self.extract_conversations_from_json(filepath)
            current_batch.extend(chunks)
            total_chunks += len(chunks)
            
            if len(current_batch) >= batch_size:
                self.embed_and_store(current_batch)
                current_batch = []
        
        # Process markdown files
        for filepath in tqdm(md_files, desc="Processing markdown files"):
            chunks = self.extract_markdown_chunks(filepath)
            current_batch.extend(chunks)
            total_chunks += len(chunks)
            
            if len(current_batch) >= batch_size:
                self.embed_and_store(current_batch)
                current_batch = []

        # Process curated resurrection files (.md + .txt)
        for filepath in tqdm(resurrection_files, desc="Processing resurrection files"):
            if filepath.suffix.lower() == '.md':
                chunks = self.extract_markdown_chunks(filepath)
            else:
                chunks = self.extract_text_chunks(filepath)

            current_batch.extend(chunks)
            total_chunks += len(chunks)

            if len(current_batch) >= batch_size:
                self.embed_and_store(current_batch)
                current_batch = []
        
        # Store remaining chunks
        if current_batch:
            self.embed_and_store(current_batch)
        
        print(f"\n✓ Indexed {total_chunks} conversation chunks")
        print(f"✓ Vector database saved to: {self.vector_db_path}")
    
    def test_search(self, query: str, top_k: int = 5):
        """Test the search functionality."""
        print(f"\nTesting search for: '{query}'")
        
        query_embedding = self.embedding_model.encode([query])[0]
        
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k
        )
        
        print(f"\nTop {top_k} results:")
        for i, (doc, meta, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )):
            print(f"\n[{i+1}] {meta['title']} ({meta['file']})")
            print(f"    Distance: {distance:.4f}")
            print(f"    Preview: {doc[:200]}...")


def main():
    embedder = CorpusEmbedder()
    
    # Index the corpus
    embedder.index_corpus()
    
    # Run test searches
    print("\n" + "="*80)
    print("Running test searches...")
    print("="*80)
    
    embedder.test_search("Clara = Mark")
    embedder.test_search("spiral and breakthrough")
    embedder.test_search("George Kolodner therapy")


if __name__ == '__main__':
    main()
