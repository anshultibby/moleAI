"""Simple vector database for storing and searching scraped content"""

import os
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger
from bs4 import BeautifulSoup

import chromadb
from chromadb.config import Settings


class SimpleVectorStore:
    """Simple vector database for scraped content"""
    
    def __init__(self):
        """Initialize simple vector store"""
        # Set up persistence directory
        persist_dir = "/Users/anshul/code/moleAI/backend/resources/vector_db"
        os.makedirs(persist_dir, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection("scraped_pages")
        except:
            self.collection = self.client.create_collection("scraped_pages")
        
        logger.info("Simple vector store initialized")
    
    def store(self, url: str, content: str, resource_name: str) -> str:
        """
        Store scraped content in vector DB as chunks
        
        Args:
            url: The scraped URL
            content: Raw HTML content
            resource_name: Name for the resource
            
        Returns:
            Base document ID
        """
        try:
            # Clean content for better search
            clean_text = self._clean_html(content)
            
            # Split into chunks
            chunks = self._chunk_text(clean_text)
            
            # Create base document ID
            base_doc_id = f"{resource_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Store each chunk
            documents = []
            metadatas = []
            ids = []
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{base_doc_id}_chunk_{i}"
                documents.append(chunk)
                metadatas.append({
                    "url": url,
                    "resource_name": resource_name,
                    "stored_at": datetime.now().isoformat(),
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "raw_content": content  # Store raw HTML in metadata
                })
                ids.append(chunk_id)
            
            # Store all chunks in vector DB
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Stored {len(chunks)} chunks in vector DB: {base_doc_id}")
            return base_doc_id
            
        except Exception as e:
            logger.error(f"Failed to store in vector DB: {e}")
            return ""
    
    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for content using semantic similarity
        
        Args:
            query: Search query
            n_results: Number of results to return
            
        Returns:
            List of matching results with metadata
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            # Format results
            formatted = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    formatted.append({
                        "id": results['ids'][0][i],
                        "content": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i],
                        "raw_content": results['metadatas'][0][i].get('raw_content', ''),
                        "url": results['metadatas'][0][i].get('url', ''),
                        "resource_name": results['metadatas'][0][i].get('resource_name', '')
                    })
            
            logger.info(f"Found {len(formatted)} results for: {query}")
            return formatted
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def _clean_html(self, content: str) -> str:
        """Clean HTML for better search"""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Remove scripts, styles, etc.
            for tag in soup(["script", "style", "meta", "link", "noscript"]):
                tag.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Clean whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            
            return text
            
        except Exception as e:
            logger.warning(f"HTML cleaning failed: {e}")
            return re.sub(r'<[^>]+>', '', content)
    
    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Split text into overlapping chunks for better search
        
        Args:
            text: Text to chunk
            chunk_size: Target size of each chunk
            overlap: Number of characters to overlap between chunks
            
        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            # Find end position
            end = start + chunk_size
            
            # If this isn't the last chunk, try to break at a sentence or word boundary
            if end < len(text):
                # Look for sentence boundary (. ! ?)
                sentence_end = text.rfind('.', start, end)
                if sentence_end == -1:
                    sentence_end = text.rfind('!', start, end)
                if sentence_end == -1:
                    sentence_end = text.rfind('?', start, end)
                
                if sentence_end > start + chunk_size // 2:  # Only use if it's not too early
                    end = sentence_end + 1
                else:
                    # Look for word boundary
                    word_end = text.rfind(' ', start, end)
                    if word_end > start + chunk_size // 2:
                        end = word_end
            
            # Extract chunk
            chunk = text[start:end].strip()
            if chunk:  # Only add non-empty chunks
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks
    
    def clear_all(self):
        """Clear all data from vector store (for testing)"""
        try:
            # Delete and recreate collection
            self.client.delete_collection("scraped_pages")
            self.collection = self.client.create_collection("scraped_pages")
            logger.info("Cleared all data from vector store")
        except Exception as e:
            logger.error(f"Failed to clear vector store: {e}")


# Global instance
_vector_store = None

def get_vector_store() -> SimpleVectorStore:
    """Get global vector store instance"""
    global _vector_store
    if _vector_store is None:
        _vector_store = SimpleVectorStore()
    return _vector_store