"""Immutable ledger for extraction records."""

import hashlib
import json
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from pathlib import Path

from interfaces.models import ExtractionResult
from edgar.config import settings


class Ledger:
    """
    Immutable record of all extractions with cryptographic integrity.
    
    Features:
    - Cryptographic hashing for integrity
    - Full lineage tracking
    - Query capabilities for analytics
    - Compliance-ready audit trail
    """
    
    def __init__(self):
        self.base_path = Path(settings.data_dir) / "ledger"
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize chain
        self.chain_file = self.base_path / "chain.jsonl"
        self.last_hash = self._get_last_hash()
    
    async def record(
        self,
        document_id: str,
        extraction_result: ExtractionResult,
        metadata: Dict
    ) -> str:
        """
        Record an extraction in the ledger.
        
        Args:
            document_id: Document identifier
            extraction_result: Complete extraction result
            metadata: Additional metadata
            
        Returns:
            Entry hash
        """
        # Create ledger entry
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "document_id": document_id,
            "goal_id": extraction_result.goal.goal_id,
            "schema_id": extraction_result.schema.id,
            "row_count": len(extraction_result.rows),
            "quality_score": self._calculate_quality_score(extraction_result),
            "metadata": metadata,
            "previous_hash": self.last_hash,
            "data_hash": self._hash_data(extraction_result.rows)
        }
        
        # Calculate entry hash
        entry_hash = self._calculate_hash(entry)
        entry["hash"] = entry_hash
        
        # Append to chain
        with open(self.chain_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
        
        # Store full result separately
        result_file = self.base_path / "results" / f"{entry_hash}.json"
        result_file.parent.mkdir(exist_ok=True)
        
        with open(result_file, "w") as f:
            json.dump(extraction_result.model_dump(), f, indent=2)
        
        # Update last hash
        self.last_hash = entry_hash
        
        return entry_hash
    
    async def query(
        self,
        document_type: Optional[str] = None,
        date_range: Optional[Tuple[str, str]] = None,
        quality_threshold: Optional[float] = None
    ) -> List[Dict]:
        """
        Query historical extractions.
        
        Args:
            document_type: Filter by document type
            date_range: Filter by date range
            quality_threshold: Minimum quality score
            
        Returns:
            List of matching entries
        """
        results = []
        
        with open(self.chain_file) as f:
            for line in f:
                entry = json.loads(line)
                
                # Apply filters
                if document_type and entry["metadata"].get("type") != document_type:
                    continue
                
                if date_range:
                    entry_date = entry["timestamp"][:10]
                    if not (date_range[0] <= entry_date <= date_range[1]):
                        continue
                
                if quality_threshold and entry["quality_score"] < quality_threshold:
                    continue
                
                results.append(entry)
        
        return results
    
    async def verify_integrity(self) -> bool:
        """
        Verify the integrity of the ledger chain.
        
        Returns:
            True if chain is valid
        """
        previous_hash = None
        
        with open(self.chain_file) as f:
            for line in f:
                entry = json.loads(line)
                
                # Check previous hash link
                if entry["previous_hash"] != previous_hash:
                    return False
                
                # Recalculate and verify hash
                stored_hash = entry["hash"]
                entry_copy = entry.copy()
                del entry_copy["hash"]
                
                calculated_hash = self._calculate_hash(entry_copy)
                if calculated_hash != stored_hash:
                    return False
                
                previous_hash = stored_hash
        
        return True
    
    async def get_entry(self, entry_hash: str) -> Optional[ExtractionResult]:
        """
        Retrieve full extraction result by hash.
        
        Args:
            entry_hash: Ledger entry hash
            
        Returns:
            Full extraction result or None
        """
        result_file = self.base_path / "results" / f"{entry_hash}.json"
        
        if result_file.exists():
            with open(result_file) as f:
                data = json.load(f)
                return ExtractionResult.model_validate(data)
        
        return None
    
    def _get_last_hash(self) -> Optional[str]:
        """Get the hash of the last entry in the chain."""
        if not self.chain_file.exists():
            return None
        
        last_line = None
        with open(self.chain_file) as f:
            for line in f:
                last_line = line
        
        if last_line:
            entry = json.loads(last_line)
            return entry["hash"]
        
        return None
    
    def _calculate_hash(self, entry: Dict) -> str:
        """Calculate SHA-256 hash of an entry."""
        # Ensure consistent ordering
        entry_str = json.dumps(entry, sort_keys=True)
        return hashlib.sha256(entry_str.encode()).hexdigest()
    
    def _hash_data(self, rows: List) -> str:
        """Calculate hash of extracted data."""
        data_str = json.dumps([row.model_dump() for row in rows], sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def _calculate_quality_score(self, result: ExtractionResult) -> float:
        """Calculate overall quality score from extraction result."""
        if not result.critic_notes:
            return 1.0
        
        scores = [
            note.score for note in result.critic_notes 
            if note.score is not None
        ]
        
        return sum(scores) / len(scores) if scores else 0.5