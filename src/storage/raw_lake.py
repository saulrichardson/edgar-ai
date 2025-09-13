"""Raw document storage lake."""

import gzip
import json
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

from edgar.config import settings


class RawLake:
    """
    Storage for original documents with compression and indexing.
    
    Features:
    - Compressed storage
    - Fast retrieval
    - Metadata indexing
    - Batch reprocessing support
    """
    
    def __init__(self):
        self.base_path = Path(settings.data_dir) / "raw_lake"
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize index
        self.index_file = self.base_path / "index.jsonl"
    
    async def store(
        self,
        content: str,
        source: str,
        metadata: Dict
    ) -> str:
        """
        Store a raw document.
        
        Args:
            content: Document content
            source: Document source (e.g., "SEC EDGAR")
            metadata: Document metadata
            
        Returns:
            Document ID
        """
        # Generate document ID
        doc_id = self._generate_doc_id(metadata)
        
        # Compress and store content
        doc_path = self._get_doc_path(doc_id)
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        
        with gzip.open(doc_path, "wt", encoding="utf-8") as f:
            f.write(content)
        
        # Update index
        index_entry = {
            "doc_id": doc_id,
            "source": source,
            "metadata": metadata,
            "stored_at": datetime.utcnow().isoformat(),
            "size_bytes": len(content),
            "compressed_size_bytes": doc_path.stat().st_size
        }
        
        with open(self.index_file, "a") as f:
            f.write(json.dumps(index_entry) + "\n")
        
        return doc_id
    
    async def retrieve(self, doc_id: str) -> Optional[Dict]:
        """
        Retrieve a document by ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document with content and metadata
        """
        # Find in index
        metadata = await self._get_metadata(doc_id)
        if not metadata:
            return None
        
        # Load content
        doc_path = self._get_doc_path(doc_id)
        
        with gzip.open(doc_path, "rt", encoding="utf-8") as f:
            content = f.read()
        
        return {
            "doc_id": doc_id,
            "content": content,
            "metadata": metadata
        }
    
    async def retrieve_batch(
        self,
        filter: Dict,
        limit: int = 100
    ) -> List[Dict]:
        """
        Retrieve multiple documents matching filter.
        
        Args:
            filter: Filter criteria
            limit: Maximum documents to return
            
        Returns:
            List of documents
        """
        matching_docs = []
        
        with open(self.index_file) as f:
            for line in f:
                entry = json.loads(line)
                
                # Apply filters
                if self._matches_filter(entry, filter):
                    doc = await self.retrieve(entry["doc_id"])
                    if doc:
                        matching_docs.append(doc)
                        
                        if len(matching_docs) >= limit:
                            break
        
        return matching_docs
    
    async def list_documents(
        self,
        source: Optional[str] = None,
        date_range: Optional[tuple] = None
    ) -> List[Dict]:
        """
        List document metadata.
        
        Args:
            source: Filter by source
            date_range: Filter by date range
            
        Returns:
            List of document metadata
        """
        documents = []
        
        with open(self.index_file) as f:
            for line in f:
                entry = json.loads(line)
                
                # Apply filters
                if source and entry["source"] != source:
                    continue
                
                if date_range:
                    stored_date = entry["stored_at"][:10]
                    if not (date_range[0] <= stored_date <= date_range[1]):
                        continue
                
                documents.append(entry)
        
        return documents
    
    async def get_statistics(self) -> Dict:
        """Get storage statistics."""
        total_docs = 0
        total_size = 0
        total_compressed = 0
        sources = {}
        
        with open(self.index_file) as f:
            for line in f:
                entry = json.loads(line)
                total_docs += 1
                total_size += entry["size_bytes"]
                total_compressed += entry["compressed_size_bytes"]
                
                source = entry["source"]
                sources[source] = sources.get(source, 0) + 1
        
        return {
            "total_documents": total_docs,
            "total_size_mb": total_size / (1024 * 1024),
            "compressed_size_mb": total_compressed / (1024 * 1024),
            "compression_ratio": total_size / total_compressed if total_compressed > 0 else 0,
            "documents_by_source": sources
        }
    
    def _generate_doc_id(self, metadata: Dict) -> str:
        """Generate document ID from metadata."""
        # Use filing info if available
        if "accession_number" in metadata:
            return metadata["accession_number"]
        
        # Otherwise use timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        form_type = metadata.get("form_type", "unknown")
        return f"{form_type}_{timestamp}"
    
    def _get_doc_path(self, doc_id: str) -> Path:
        """Get storage path for document."""
        # Partition by first few characters for better file system performance
        partition = doc_id[:4] if len(doc_id) >= 4 else "misc"
        return self.base_path / "documents" / partition / f"{doc_id}.gz"
    
    async def _get_metadata(self, doc_id: str) -> Optional[Dict]:
        """Get metadata for a document."""
        with open(self.index_file) as f:
            for line in f:
                entry = json.loads(line)
                if entry["doc_id"] == doc_id:
                    return entry
        
        return None
    
    def _matches_filter(self, entry: Dict, filter: Dict) -> bool:
        """Check if entry matches filter criteria."""
        for key, value in filter.items():
            if key in entry:
                if entry[key] != value:
                    return False
            elif key in entry.get("metadata", {}):
                if entry["metadata"][key] != value:
                    return False
            else:
                return False
        
        return True