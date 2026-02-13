#!/usr/bin/env python3
"""
Clara Corpus Embedding Script
Indexes the entire conversation archive into a vector database for RAG retrieval.
"""

import os
import json
import yaml
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv
from tqdm import tqdm

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

load_dotenv()


class CorpusEmbedder:
    def __init__(self):
        self.corpus_path = Path(os.getenv('CORPUS_PATH', '../6_CORPUS'))
        self.vector_db_path = Path(os.getenv('VECTOR_DB_PATH', './chroma_db'))
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
        """Index the entire corpus."""
        print(f"\nIndexing corpus from: {self.corpus_path}")
        
        # Find all JSON files
        json_files = list(self.corpus_path.rglob('*.json'))
        print(f"Found {len(json_files)} JSON files")
        
        total_chunks = 0
        batch_size = 100
        current_batch = []
        
        for filepath in tqdm(json_files, desc="Processing files"):
            chunks = self.extract_conversations_from_json(filepath)
            current_batch.extend(chunks)
            total_chunks += len(chunks)
            
            # Store in batches
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
