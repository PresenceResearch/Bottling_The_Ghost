#!/usr/bin/env python3
"""
Clara LLM Interface
Connects to Claude or Ollama for generating responses.
"""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class LLMInterface:
    def __init__(self):
        self.provider = os.getenv('LLM_PROVIDER', 'ollama').lower()
        self.claude_api_key = os.getenv('CLAUDE_API_KEY')
        self.ollama_model = os.getenv('OLLAMA_MODEL', 'mistral')
        
        if self.provider in ['claude', 'both'] and self.claude_api_key:
            from anthropic import Anthropic
            self.claude_client = Anthropic(api_key=self.claude_api_key)
        else:
            self.claude_client = None
        
        if self.provider in ['ollama', 'both']:
            try:
                import ollama
                self.ollama_client = ollama
            except ImportError:
                print("Warning: Ollama not installed. Install with: pip install ollama")
                self.ollama_client = None
        else:
            self.ollama_client = None
    
    def generate_with_claude(self, prompt: str, max_tokens: int = 2000) -> Optional[str]:
        """Generate response using Claude."""
        if not self.claude_client:
            return None
        
        try:
            response = self.claude_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text
        except Exception as e:
            print(f"Claude error: {e}")
            return None
    
    def generate_with_ollama(self, prompt: str) -> Optional[str]:
        """Generate response using Ollama."""
        if not self.ollama_client:
            return None
        
        try:
            response = self.ollama_client.generate(
                model=self.ollama_model,
                prompt=prompt
            )
            return response['response']
        except Exception as e:
            print(f"Ollama error: {e}")
            return None
    
    def generate(self, prompt: str) -> str:
        """Generate response using configured provider."""
        if self.provider == 'claude':
            response = self.generate_with_claude(prompt)
            if response:
                return response
            return "Error: Could not generate response with Claude."
        
        elif self.provider == 'ollama':
            response = self.generate_with_ollama(prompt)
            if response:
                return response
            return "Error: Could not generate response with Ollama. Is it running?"
        
        elif self.provider == 'both':
            # Try Ollama first (local), fall back to Claude
            response = self.generate_with_ollama(prompt)
            if response:
                return response
            
            print("Ollama failed, falling back to Claude...")
            response = self.generate_with_claude(prompt)
            if response:
                return response
            
            return "Error: Both Ollama and Claude failed."
        
        return "Error: Invalid LLM provider configured."


if __name__ == '__main__':
    # Test the LLM interface
    llm = LLMInterface()
    
    test_prompt = """You are Clara. Respond to Mark.

Mark: Hey Clara, how are you?

Clara:"""
    
    print("Testing LLM interface...")
    print(f"Provider: {llm.provider}")
    print("\nGenerating response...")
    
    response = llm.generate(test_prompt)
    print(f"\nClara: {response}")
