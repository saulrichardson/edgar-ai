"""Ontology store for domain knowledge."""

from typing import List, Dict, Set, Optional
from pathlib import Path
import json

from edgar.config import settings


class Ontology:
    """
    Build and maintain domain knowledge graph.
    
    Features:
    - Track concept relationships
    - Identify synonyms and aliases
    - Build hierarchical taxonomies
    - Enable semantic search
    """
    
    def __init__(self):
        self.base_path = Path(settings.data_dir) / "ontology"
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Load existing ontology
        self.concepts = self._load_concepts()
        self.relationships = self._load_relationships()
    
    async def add_concept(
        self,
        name: str,
        category: str,
        aliases: List[str] = None,
        related_to: List[str] = None,
        description: Optional[str] = None
    ) -> str:
        """
        Add a concept to the ontology.
        
        Args:
            name: Concept name
            category: Concept category
            aliases: Alternative names
            related_to: Related concepts
            description: Concept description
            
        Returns:
            Concept ID
        """
        concept_id = self._generate_id(name)
        
        concept = {
            "id": concept_id,
            "name": name,
            "category": category,
            "aliases": aliases or [],
            "description": description,
            "frequency": 1
        }
        
        # Store concept
        self.concepts[concept_id] = concept
        
        # Store relationships
        if related_to:
            for related_id in related_to:
                self._add_relationship(concept_id, related_id, "related_to")
        
        # Save to disk
        await self._save_concepts()
        
        return concept_id
    
    async def find_related(
        self,
        concept_name: str,
        max_depth: int = 2
    ) -> List[Dict]:
        """
        Find concepts related to a given concept.
        
        Args:
            concept_name: Starting concept
            max_depth: Maximum traversal depth
            
        Returns:
            List of related concepts with distance
        """
        # Find concept ID
        concept_id = self._find_concept_id(concept_name)
        if not concept_id:
            return []
        
        # BFS to find related concepts
        visited = set()
        queue = [(concept_id, 0)]
        related = []
        
        while queue:
            current_id, depth = queue.pop(0)
            
            if current_id in visited or depth > max_depth:
                continue
            
            visited.add(current_id)
            
            if current_id != concept_id:
                concept = self.concepts.get(current_id)
                if concept:
                    related.append({
                        "concept": concept,
                        "distance": depth
                    })
            
            # Add neighbors
            if depth < max_depth:
                neighbors = self._get_neighbors(current_id)
                for neighbor_id in neighbors:
                    queue.append((neighbor_id, depth + 1))
        
        return related
    
    async def merge_concepts(
        self,
        concept1: str,
        concept2: str
    ) -> str:
        """
        Merge two concepts that are synonyms.
        
        Args:
            concept1: First concept
            concept2: Second concept
            
        Returns:
            Merged concept ID
        """
        id1 = self._find_concept_id(concept1)
        id2 = self._find_concept_id(concept2)
        
        if not id1 or not id2:
            raise ValueError("Concepts not found")
        
        # Merge into first concept
        c1 = self.concepts[id1]
        c2 = self.concepts[id2]
        
        # Combine aliases
        c1["aliases"].extend([c2["name"]] + c2["aliases"])
        c1["aliases"] = list(set(c1["aliases"]))
        
        # Combine frequency
        c1["frequency"] += c2["frequency"]
        
        # Transfer relationships
        for (from_id, to_id, rel_type) in self.relationships:
            if from_id == id2:
                self._add_relationship(id1, to_id, rel_type)
            elif to_id == id2:
                self._add_relationship(from_id, id1, rel_type)
        
        # Remove old concept
        del self.concepts[id2]
        self.relationships = [
            rel for rel in self.relationships 
            if id2 not in rel[:2]
        ]
        
        await self._save_concepts()
        return id1
    
    async def get_taxonomy(self, category: str) -> Dict:
        """
        Get hierarchical taxonomy for a category.
        
        Args:
            category: Category name
            
        Returns:
            Taxonomy tree
        """
        # Find all concepts in category
        category_concepts = [
            c for c in self.concepts.values() 
            if c["category"] == category
        ]
        
        # Build hierarchy based on relationships
        taxonomy = {
            "category": category,
            "concepts": [],
            "subcategories": {}
        }
        
        for concept in category_concepts:
            # Simple taxonomy - would be more sophisticated in production
            taxonomy["concepts"].append({
                "name": concept["name"],
                "aliases": concept["aliases"],
                "frequency": concept["frequency"]
            })
        
        return taxonomy
    
    async def search(self, query: str) -> List[Dict]:
        """
        Search concepts by name or alias.
        
        Args:
            query: Search query
            
        Returns:
            Matching concepts
        """
        query_lower = query.lower()
        matches = []
        
        for concept in self.concepts.values():
            # Check name
            if query_lower in concept["name"].lower():
                matches.append(concept)
                continue
            
            # Check aliases
            for alias in concept["aliases"]:
                if query_lower in alias.lower():
                    matches.append(concept)
                    break
        
        return matches
    
    def _generate_id(self, name: str) -> str:
        """Generate concept ID from name."""
        return name.lower().replace(" ", "_").replace("-", "_")
    
    def _find_concept_id(self, name: str) -> Optional[str]:
        """Find concept ID by name or alias."""
        name_lower = name.lower()
        
        for concept_id, concept in self.concepts.items():
            if concept["name"].lower() == name_lower:
                return concept_id
            
            for alias in concept["aliases"]:
                if alias.lower() == name_lower:
                    return concept_id
        
        return None
    
    def _add_relationship(
        self,
        from_id: str,
        to_id: str,
        rel_type: str
    ) -> None:
        """Add a relationship between concepts."""
        rel = (from_id, to_id, rel_type)
        if rel not in self.relationships:
            self.relationships.append(rel)
    
    def _get_neighbors(self, concept_id: str) -> Set[str]:
        """Get all neighbors of a concept."""
        neighbors = set()
        
        for from_id, to_id, _ in self.relationships:
            if from_id == concept_id:
                neighbors.add(to_id)
            elif to_id == concept_id:
                neighbors.add(from_id)
        
        return neighbors
    
    def _load_concepts(self) -> Dict:
        """Load concepts from disk."""
        concept_file = self.base_path / "concepts.json"
        
        if concept_file.exists():
            with open(concept_file) as f:
                return json.load(f)
        
        return {}
    
    def _load_relationships(self) -> List:
        """Load relationships from disk."""
        rel_file = self.base_path / "relationships.json"
        
        if rel_file.exists():
            with open(rel_file) as f:
                return json.load(f)
        
        return []
    
    async def _save_concepts(self) -> None:
        """Save concepts and relationships to disk."""
        concept_file = self.base_path / "concepts.json"
        rel_file = self.base_path / "relationships.json"
        
        with open(concept_file, "w") as f:
            json.dump(self.concepts, f, indent=2)
        
        with open(rel_file, "w") as f:
            json.dump(self.relationships, f, indent=2)