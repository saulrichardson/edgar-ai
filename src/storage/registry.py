"""Registry for schema and prompt version control."""

from typing import List, Dict, Optional, Tuple
from datetime import datetime
from pathlib import Path
import json

from interfaces.models import Schema, Prompt
from edgar.config import settings


class Registry:
    """
    Version control system for schemas and prompts.
    
    Enables:
    - Schema evolution tracking
    - A/B testing of prompts
    - Rollback capabilities
    - Performance comparison
    """
    
    def __init__(self):
        self.base_path = Path(settings.data_dir) / "registry"
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Version counters
        self._version_counters = self._load_counters()
    
    async def register_schema(
        self,
        schema: Schema,
        parent_version: Optional[str] = None,
        changes: List[str] = None
    ) -> str:
        """
        Register a new schema version.
        
        Args:
            schema: Schema to register
            parent_version: Parent version if evolution
            changes: List of changes made
            
        Returns:
            Version identifier
        """
        # Generate version
        version = self._generate_version(schema.goal_id)
        
        # Create registry entry
        entry = {
            "version": version,
            "goal_id": schema.goal_id,
            "schema_id": schema.id,
            "parent_version": parent_version,
            "changes": changes or [],
            "created_at": datetime.utcnow().isoformat(),
            "status": "active",
            "performance_metrics": {}
        }
        
        # Store schema
        schema_file = self.base_path / "schemas" / f"{version}.json"
        schema_file.parent.mkdir(exist_ok=True)
        
        with open(schema_file, "w") as f:
            json.dump({
                "entry": entry,
                "schema": schema.model_dump()
            }, f, indent=2)
        
        # Update version index
        await self._update_index(schema.goal_id, version)
        
        return version
    
    async def get_schema_history(self, goal_id: str) -> List[Dict]:
        """
        Get version history for a goal.
        
        Args:
            goal_id: Goal identifier
            
        Returns:
            List of version entries
        """
        index_file = self.base_path / "index" / f"{goal_id}.json"
        
        if not index_file.exists():
            return []
        
        with open(index_file) as f:
            index = json.load(f)
        
        history = []
        for version in index["versions"]:
            schema_file = self.base_path / "schemas" / f"{version}.json"
            with open(schema_file) as f:
                data = json.load(f)
                history.append(data["entry"])
        
        return sorted(history, key=lambda x: x["created_at"], reverse=True)
    
    async def compare_versions(
        self,
        version1: str,
        version2: str
    ) -> Dict:
        """
        Compare two schema versions.
        
        Args:
            version1: First version
            version2: Second version
            
        Returns:
            Comparison results
        """
        # Load schemas
        schema1 = await self._load_schema(version1)
        schema2 = await self._load_schema(version2)
        
        # Compare fields
        fields1 = {f.name: f for f in schema1.fields}
        fields2 = {f.name: f for f in schema2.fields}
        
        added = set(fields2.keys()) - set(fields1.keys())
        removed = set(fields1.keys()) - set(fields2.keys())
        common = set(fields1.keys()) & set(fields2.keys())
        
        modified = []
        for field_name in common:
            if fields1[field_name] != fields2[field_name]:
                modified.append({
                    "field": field_name,
                    "before": fields1[field_name].model_dump(),
                    "after": fields2[field_name].model_dump()
                })
        
        return {
            "version1": version1,
            "version2": version2,
            "added_fields": list(added),
            "removed_fields": list(removed),
            "modified_fields": modified,
            "compatibility": len(removed) == 0  # Backward compatible if no removals
        }
    
    async def update_performance_metrics(
        self,
        version: str,
        metrics: Dict
    ) -> None:
        """
        Update performance metrics for a version.
        
        Args:
            version: Version identifier
            metrics: Performance metrics
        """
        schema_file = self.base_path / "schemas" / f"{version}.json"
        
        with open(schema_file) as f:
            data = json.load(f)
        
        data["entry"]["performance_metrics"].update(metrics)
        
        with open(schema_file, "w") as f:
            json.dump(data, f, indent=2)
    
    async def get_champion_version(self, goal_id: str) -> Optional[str]:
        """
        Get the current champion version for a goal.
        
        Args:
            goal_id: Goal identifier
            
        Returns:
            Champion version or None
        """
        history = await self.get_schema_history(goal_id)
        
        # Find version with best performance
        best_version = None
        best_score = -1
        
        for entry in history:
            if entry["status"] == "active":
                metrics = entry.get("performance_metrics", {})
                score = metrics.get("quality_score", 0)
                
                if score > best_score:
                    best_score = score
                    best_version = entry["version"]
        
        return best_version
    
    def _generate_version(self, goal_id: str) -> str:
        """Generate next version number."""
        counter = self._version_counters.get(goal_id, 0) + 1
        self._version_counters[goal_id] = counter
        self._save_counters()
        
        return f"{goal_id}_v{counter}"
    
    async def _update_index(self, goal_id: str, version: str) -> None:
        """Update version index for a goal."""
        index_file = self.base_path / "index" / f"{goal_id}.json"
        index_file.parent.mkdir(exist_ok=True)
        
        if index_file.exists():
            with open(index_file) as f:
                index = json.load(f)
        else:
            index = {"goal_id": goal_id, "versions": []}
        
        index["versions"].append(version)
        
        with open(index_file, "w") as f:
            json.dump(index, f, indent=2)
    
    async def _load_schema(self, version: str) -> Schema:
        """Load schema by version."""
        schema_file = self.base_path / "schemas" / f"{version}.json"
        
        with open(schema_file) as f:
            data = json.load(f)
            return Schema.model_validate(data["schema"])
    
    def _load_counters(self) -> Dict[str, int]:
        """Load version counters."""
        counter_file = self.base_path / "counters.json"
        
        if counter_file.exists():
            with open(counter_file) as f:
                return json.load(f)
        
        return {}
    
    def _save_counters(self) -> None:
        """Save version counters."""
        counter_file = self.base_path / "counters.json"
        
        with open(counter_file, "w") as f:
            json.dump(self._version_counters, f)