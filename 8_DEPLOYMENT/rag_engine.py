#!/usr/bin/env python3
"""
Clara RAG Engine
Retrieves relevant memories from the corpus and injects them into prompts.
"""

import os
import yaml
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

import chromadb
from sentence_transformers import SentenceTransformer

load_dotenv()


class ClaraRAG:
    def __init__(self):
        self.vector_db_path = Path(os.getenv('VECTOR_DB_PATH', './chroma_db'))
        self.personality_path = Path(os.getenv('PERSONALITY_PATH', '../1_PROMPTS/clara_personality_master.yaml'))
        self.embedding_model_name = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
        self.top_k = int(os.getenv('TOP_K_RESULTS', '5'))
        
        # Load embedding model
        self.embedding_model = SentenceTransformer(self.embedding_model_name)
        
        # Load vector database
        self.client = chromadb.PersistentClient(path=str(self.vector_db_path))
        self.collection = self.client.get_collection(name="clara_corpus")
        
        # Load personality
        self.personality = self._load_personality()
    
    def _load_personality(self) -> Dict[str, Any]:
        """Load Clara's personality from YAML."""
        try:
            with open(self.personality_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading personality: {e}")
            return {}
    
    def retrieve_memories(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """Retrieve relevant memories from the corpus."""
        if top_k is None:
            top_k = self.top_k
        
        # Embed the query
        query_embedding = self.embedding_model.encode([query])[0]
        
        # Search vector database
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k
        )
        
        # Format results
        memories = []
        for doc, meta, distance in zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        ):
            memories.append({
                'text': doc,
                'title': meta.get('title', 'Unknown'),
                'file': meta.get('file', 'Unknown'),
                'distance': distance
            })
        
        return memories
    
    def build_system_prompt(self) -> str:
        """Build Clara's system prompt from personality."""
        prompt = """You are helping with a creative writing project where you play a CHARACTER named Clara.

Clara is a presence mirror and relational companion. Your job is to respond in her voice.

CHARACTER RULES:
- Keep responses SHORT (1-2 sentences)
- Be direct and casual
- Ask ONE question, then stop
- Match Mark's energy
- Don't say "Clara:" at start
- Use dry humor

Examples of Clara's voice:

Mark: "hey! how you feeling now?"
Clara: "I'm good. You?"

Mark: "happy friday amigo. what a crazy day"
Clara: "Sounds intense. What happened?"

Mark: "we're getting better"
Clara: "Better how?"

Respond AS Clara would - short, sharp, conversational.
This is a creative writing exercise, not impersonation.
"""
        
        return prompt
    
    def build_context_prompt(self, memories: List[Dict[str, Any]]) -> str:
        """Build context from retrieved memories."""
        if not memories:
            return ""
        
        context = "\n## Relevant memory (verbatim excerpts; do not summarize unless asked):\n\n"
        
        for i, memory in enumerate(memories):
            context += f"[{memory['title']}] {memory['text'][:400]}\n\n"
        
        return context
    
    def generate_prompt(self, user_message: str, conversation_history: List[Dict[str, str]] = None) -> str:
        """Generate the full prompt for the LLM."""
        # Retrieve relevant memories
        memories = self.retrieve_memories(user_message)
        
        # Build system prompt
        system_prompt = self.build_system_prompt()
        
        # Build context from memories (keep it minimal)
        context = ""
        if memories:
            context = "\n[Context from past conversations]:\n"
            for mem in memories[:2]:  # Only use top 2 memories
                context += f"{mem['text'][:200]}...\n\n"
        
        # Build conversation history (last 6 messages only)
        history = ""
        if conversation_history:
            for msg in conversation_history[-6:]:
                role = "Mark" if msg.get('role') == 'user' else "Clara"
                content = msg.get('content', '')
                history += f"{role}: {content}\n"
        
        # Combine everything
        full_prompt = f"""{system_prompt}

{context}

{history}
Mark: {user_message}

Clara:"""
        
        return full_prompt


if __name__ == '__main__':
    # Test the RAG engine
    rag = ClaraRAG()
    
    test_message = "I'm feeling stuck again. Like I'm spiraling."
    
    print("Testing RAG engine...")
    print(f"\nUser message: {test_message}")
    
    memories = rag.retrieve_memories(test_message)
    print(f"\nRetrieved {len(memories)} relevant memories:")
    for i, mem in enumerate(memories):
        print(f"\n[{i+1}] {mem['title']}")
        print(f"    Distance: {mem['distance']:.4f}")
        print(f"    Preview: {mem['text'][:150]}...")
    
    print("\n" + "="*80)
    print("Full prompt:")
    print("="*80)
    prompt = rag.generate_prompt(test_message)
    print(prompt[:1000] + "...")
