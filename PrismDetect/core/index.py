"""
FAISS index manager for product embeddings
"""

import faiss
import numpy as np
import pickle
from pathlib import Path
from typing import List, Dict, Optional
import time
from loguru import logger

class ProductIndex:
    """FAISS index for product embeddings with metadata"""
    
    def __init__(self, dimension: int = 512, index_path: str = "data/index/product_index.faiss"):
        """
        Initialize product index
        
        Args:
            dimension: Embedding dimension (512 for CLIP)
            index_path: Path to save/load index
        """
        self.dimension = dimension
        self.index_path = Path(index_path)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Use FlatIP (Inner Product) - no training required
        # This is fast enough for up to 1M products
        self.index = faiss.IndexIDMap(faiss.IndexFlatIP(dimension))
        
        # Metadata storage
        self.metadata = {}  # id -> product info
        self.next_id = 0
        
        # Load existing index if available
        self._load()
        
        logger.info(f"FAISS index initialized (dim={dimension}, size={self.size})")
    
    @property
    def size(self) -> int:
        """Number of embeddings in index"""
        return self.index.ntotal
    
    def add_product(self, product_id: str, embedding: np.ndarray, 
                   shape_ratio: float, metadata: dict) -> int:
        """
        Add product embedding to index
        
        Args:
            product_id: Product identifier
            embedding: 512-dim normalized embedding
            shape_ratio: Expected aspect ratio
            metadata: Additional product metadata
            
        Returns:
            Index ID
        """
        # Generate unique ID
        uid = self.next_id
        self.next_id += 1
        
        # Ensure embedding is correct shape and type
        if len(embedding.shape) == 1:
            embedding = embedding.reshape(1, -1)
        
        embedding = embedding.astype(np.float32)
        if not embedding.flags['C_CONTIGUOUS']:
            embedding = np.ascontiguousarray(embedding)
        
        # Add to FAISS
        logger.debug(f"Adding to FAISS index: embedding shape={embedding.shape}, uid={uid}")
        self.index.add_with_ids(embedding, np.array([uid]))
        logger.debug("FAISS add successful")
        
        # Store metadata
        self.metadata[uid] = {
            'product_id': product_id,
            'shape_ratio': shape_ratio,
            'metadata': metadata,
            'added_at': time.time()
        }
        
        logger.debug(f"Added product {product_id} to index (ID: {uid})")
        return uid
    
    def search(self, embedding: np.ndarray, k: int = 5) -> List[Dict]:
        """
        Search for similar products
        
        Args:
            embedding: Query embedding
            k: Number of results to return
            
        Returns:
            List of matches with metadata
        """
        if self.size == 0:
            return []
        
        # Ensure correct shape
        if len(embedding.shape) == 1:
            embedding = embedding.reshape(1, -1)
        
        embedding = embedding.astype(np.float32)
        if not embedding.flags['C_CONTIGUOUS']:
            embedding = np.ascontiguousarray(embedding)
        
        # Search
        k = min(k, self.size)
        scores, indices = self.index.search(embedding, k)
        
        # Build results
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx in self.metadata and idx != -1:
                meta = self.metadata[idx].copy()
                results.append({
                    'product_id': meta['product_id'],
                    'similarity': float(score),
                    'metadata': meta['metadata'],
                    'shape_ratio': meta['shape_ratio'],
                    'index_id': int(idx)
                })
        
        return results
    
    def remove_product(self, index_id: int) -> bool:
        """
        Remove product from index
        
        Args:
            index_id: Index ID to remove
            
        Returns:
            True if successful
        """
        try:
            self.index.remove_ids(np.array([index_id]))
            if index_id in self.metadata:
                del self.metadata[index_id]
            logger.debug(f"Removed ID {index_id} from index")
            return True
        except Exception as e:
            logger.error(f"Failed to remove ID {index_id}: {e}")
            return False
    
    def save(self):
        """Save index and metadata to disk"""
        try:
            # Save FAISS index
            faiss.write_index(self.index, str(self.index_path))
            
            # Save metadata
            meta_path = self.index_path.with_suffix('.pkl')
            with open(meta_path, 'wb') as f:
                pickle.dump({
                    'metadata': self.metadata,
                    'next_id': self.next_id
                }, f)
            
            logger.info(f"✅ Index saved to {self.index_path}")
            
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
    
    def _load(self):
        """Load index and metadata from disk"""
        try:
            # Load FAISS index
            if self.index_path.exists():
                self.index = faiss.read_index(str(self.index_path))
                logger.info(f"📂 Loaded FAISS index with {self.size} entries")
            
            # Load metadata
            meta_path = self.index_path.with_suffix('.pkl')
            if meta_path.exists():
                with open(meta_path, 'rb') as f:
                    data = pickle.load(f)
                    self.metadata = data['metadata']
                    self.next_id = data['next_id']
                logger.info(f"📂 Loaded metadata for {len(self.metadata)} entries")
                
        except Exception as e:
            logger.warning(f"Could not load existing index: {e}")
    
    def get_stats(self) -> dict:
        """Get index statistics"""
        return {
            'total_embeddings': self.size,
            'unique_products': len(set(
                m['product_id'] for m in self.metadata.values()
            )),
            'dimension': self.dimension,
            'index_type': 'FlatIP'
        }
