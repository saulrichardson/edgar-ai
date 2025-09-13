"""Snapshot storage for debugging and compliance."""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional, List

from edgar.config import settings


class SnapshotStore:
    """
    Point-in-time system state capture for debugging and compliance.
    
    Use cases:
    - Debugging extraction issues
    - Compliance documentation
    - Performance analysis
    - Reproducibility
    """
    
    def __init__(self):
        self.base_path = Path(settings.data_dir) / "snapshots"
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self.retention_days = getattr(settings, "snapshot_retention_days", 90)
    
    async def create(
        self,
        extraction_id: str,
        state: Dict
    ) -> str:
        """
        Create a snapshot of extraction state.
        
        Args:
            extraction_id: Extraction identifier
            state: Complete state to snapshot
            
        Returns:
            Snapshot ID
        """
        # Generate snapshot ID
        timestamp = datetime.utcnow()
        snapshot_id = f"{extraction_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        # Create snapshot
        snapshot = {
            "id": snapshot_id,
            "extraction_id": extraction_id,
            "timestamp": timestamp.isoformat(),
            "state": state,
            "metadata": {
                "version": "2.0",
                "retention_until": (timestamp + timedelta(days=self.retention_days)).isoformat()
            }
        }
        
        # Store snapshot
        snapshot_path = self._get_snapshot_path(snapshot_id)
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(snapshot_path, "w") as f:
            json.dump(snapshot, f, indent=2)
        
        # Update index
        await self._update_index(snapshot_id, extraction_id)
        
        return snapshot_id
    
    async def restore(self, snapshot_id: str) -> Optional[Dict]:
        """
        Restore a snapshot.
        
        Args:
            snapshot_id: Snapshot ID
            
        Returns:
            Snapshot state or None
        """
        snapshot_path = self._get_snapshot_path(snapshot_id)
        
        if not snapshot_path.exists():
            return None
        
        with open(snapshot_path) as f:
            snapshot = json.load(f)
        
        return snapshot["state"]
    
    async def list_snapshots(
        self,
        extraction_id: Optional[str] = None,
        date_range: Optional[tuple] = None
    ) -> List[Dict]:
        """
        List available snapshots.
        
        Args:
            extraction_id: Filter by extraction
            date_range: Filter by date range
            
        Returns:
            List of snapshot metadata
        """
        index_file = self.base_path / "index.jsonl"
        
        if not index_file.exists():
            return []
        
        snapshots = []
        
        with open(index_file) as f:
            for line in f:
                entry = json.loads(line)
                
                # Apply filters
                if extraction_id and entry["extraction_id"] != extraction_id:
                    continue
                
                if date_range:
                    snapshot_date = entry["timestamp"][:10]
                    if not (date_range[0] <= snapshot_date <= date_range[1]):
                        continue
                
                snapshots.append(entry)
        
        return sorted(snapshots, key=lambda x: x["timestamp"], reverse=True)
    
    async def cleanup_expired(self) -> int:
        """
        Remove expired snapshots.
        
        Returns:
            Number of snapshots removed
        """
        current_time = datetime.utcnow()
        removed_count = 0
        
        # Get all snapshots
        snapshots = await self.list_snapshots()
        
        for snapshot_meta in snapshots:
            snapshot_id = snapshot_meta["id"]
            snapshot_path = self._get_snapshot_path(snapshot_id)
            
            if snapshot_path.exists():
                with open(snapshot_path) as f:
                    snapshot = json.load(f)
                
                retention_until = datetime.fromisoformat(
                    snapshot["metadata"]["retention_until"]
                )
                
                if current_time > retention_until:
                    snapshot_path.unlink()
                    removed_count += 1
        
        # Rebuild index after cleanup
        if removed_count > 0:
            await self._rebuild_index()
        
        return removed_count
    
    async def analyze_snapshot(self, snapshot_id: str) -> Dict:
        """
        Analyze a snapshot for debugging.
        
        Args:
            snapshot_id: Snapshot ID
            
        Returns:
            Analysis results
        """
        state = await self.restore(snapshot_id)
        
        if not state:
            return {"error": "Snapshot not found"}
        
        analysis = {
            "snapshot_id": snapshot_id,
            "prompt_length": len(state.get("prompt", "")),
            "response_length": len(str(state.get("model_response", ""))),
            "extracted_rows": len(state.get("extracted_data", [])),
            "critic_notes": len(state.get("critic_feedback", [])),
            "has_errors": any(
                note.get("severity") == "error" 
                for note in state.get("critic_feedback", [])
            )
        }
        
        # Analyze specific issues
        if state.get("critic_feedback"):
            error_fields = [
                note["field_name"] 
                for note in state["critic_feedback"] 
                if note.get("severity") == "error"
            ]
            analysis["error_fields"] = list(set(error_fields))
        
        return analysis
    
    def _get_snapshot_path(self, snapshot_id: str) -> Path:
        """Get storage path for snapshot."""
        # Partition by date for better organization
        date_part = snapshot_id.split("_")[1] if "_" in snapshot_id else "unknown"
        return self.base_path / date_part / f"{snapshot_id}.json"
    
    async def _update_index(self, snapshot_id: str, extraction_id: str) -> None:
        """Update snapshot index."""
        index_file = self.base_path / "index.jsonl"
        
        entry = {
            "id": snapshot_id,
            "extraction_id": extraction_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        with open(index_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
    
    async def _rebuild_index(self) -> None:
        """Rebuild index from existing snapshots."""
        index_file = self.base_path / "index.jsonl"
        new_entries = []
        
        # Scan all snapshot files
        for snapshot_file in self.base_path.rglob("*.json"):
            if snapshot_file.name == "index.jsonl":
                continue
            
            try:
                with open(snapshot_file) as f:
                    snapshot = json.load(f)
                
                new_entries.append({
                    "id": snapshot["id"],
                    "extraction_id": snapshot["extraction_id"],
                    "timestamp": snapshot["timestamp"]
                })
            except:
                # Skip corrupted files
                pass
        
        # Write new index
        with open(index_file, "w") as f:
            for entry in sorted(new_entries, key=lambda x: x["timestamp"]):
                f.write(json.dumps(entry) + "\n")