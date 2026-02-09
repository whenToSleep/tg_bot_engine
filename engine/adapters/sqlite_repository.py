"""SQLite implementation of the EntityRepository.

This module provides a concrete repository implementation using SQLite
as the persistent storage backend. Features include:
- Optimistic locking via version numbers
- Automatic schema creation
- JSON serialization of entity data
- Efficient indexing by entity type
"""

import sqlite3
import json
from typing import Optional, List, Dict, Any
from pathlib import Path

from engine.core.repository import EntityRepository


class SQLiteRepository(EntityRepository):
    """Repository implementation using SQLite database.
    
    Stores entities as JSON blobs with metadata including:
    - entity_id (primary key)
    - entity_type (indexed for fast queries)
    - data (JSON serialized entity data)
    - version (for optimistic locking)
    - updated_at (timestamp)
    
    Example:
        >>> repo = SQLiteRepository("game.db")
        >>> repo.save("player_1", {"_type": "player", "gold": 100, "_version": 1})
        >>> data = repo.load("player_1")
        >>> print(data["gold"])
        100
    """
    
    def __init__(self, db_path: str = "game.db"):
        """Initialize SQLite repository.
        
        Args:
            db_path: Path to SQLite database file (will be created if doesn't exist)
        """
        self.db_path = str(Path(db_path).resolve())
        self._init_db()
    
    def _init_db(self) -> None:
        """Create database schema if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create entities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                entity_id TEXT PRIMARY KEY,
                entity_type TEXT NOT NULL,
                data TEXT NOT NULL,
                version INTEGER NOT NULL DEFAULT 1,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create index on entity_type for fast filtering
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_entity_type 
            ON entities(entity_type)
        """)
        
        conn.commit()
        conn.close()
    
    def save(self, entity_id: str, entity_data: dict) -> None:
        """Save entity with optimistic locking.
        
        Uses version numbers to prevent concurrent modification conflicts.
        If the version in storage doesn't match the version being saved,
        a ValueError is raised.
        
        Args:
            entity_id: Unique identifier of the entity
            entity_data: Dictionary containing entity data (must include _type and _version)
            
        Raises:
            ValueError: If optimistic lock fails (version mismatch)
            KeyError: If entity_data is missing required fields
        """
        entity_type = entity_data.get('_type', 'unknown')
        current_version = entity_data.get('_version', 1)
        
        # Serialize data to JSON
        data_json = json.dumps(entity_data, ensure_ascii=False)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if entity exists
        cursor.execute("SELECT version FROM entities WHERE entity_id = ?", (entity_id,))
        existing = cursor.fetchone()
        
        if existing is None:
            # Insert new entity
            cursor.execute("""
                INSERT INTO entities (entity_id, entity_type, data, version)
                VALUES (?, ?, ?, ?)
            """, (entity_id, entity_type, data_json, current_version))
        else:
            # Update existing entity with optimistic lock check
            existing_version = existing[0]
            if existing_version != current_version:
                conn.close()
                raise ValueError(
                    f"Optimistic lock failed for {entity_id}: "
                    f"expected version {current_version}, but found {existing_version}"
                )
            
            new_version = current_version + 1
            entity_data['_version'] = new_version
            data_json = json.dumps(entity_data, ensure_ascii=False)
            
            cursor.execute("""
                UPDATE entities 
                SET data = ?, version = ?, updated_at = CURRENT_TIMESTAMP
                WHERE entity_id = ? AND version = ?
            """, (data_json, new_version, entity_id, current_version))
            
            if cursor.rowcount == 0:
                conn.close()
                raise ValueError(f"Optimistic lock failed for {entity_id}")
        
        conn.commit()
        conn.close()
    
    def load(self, entity_id: str) -> Optional[dict]:
        """Load entity from database.
        
        Args:
            entity_id: Unique identifier of the entity
            
        Returns:
            Dictionary with entity data including _version, or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT data, version FROM entities WHERE entity_id = ?
        """, (entity_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row is None:
            return None
        
        # Deserialize JSON and add version
        data = json.loads(row[0])
        data['_version'] = row[1]
        return data
    
    def load_bulk(self, entity_ids: List[str]) -> dict[str, dict]:
        """Load multiple entities in a single database query.
        
        Optimized for loading collections (e.g., player's deck of 30 cards).
        Uses SQL IN clause instead of individual queries.
        
        Args:
            entity_ids: List of entity IDs to load
            
        Returns:
            Dictionary mapping entity_id -> entity_data
            Missing entities are not included in the result.
            
        Example:
            >>> repo = SQLiteRepository("game.db")
            >>> deck_ids = ["card_1", "card_2", "card_3"]
            >>> cards = repo.load_bulk(deck_ids)
            >>> for card_id, card_data in cards.items():
            ...     print(f"{card_id}: {card_data['name']}")
            
        Note:
            This is ~10-30x faster than individual load() calls for collections.
        """
        if not entity_ids:
            return {}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build SQL with placeholders for IN clause
        placeholders = ','.join('?' * len(entity_ids))
        query = f"""
            SELECT entity_id, data, version 
            FROM entities 
            WHERE entity_id IN ({placeholders})
        """
        
        cursor.execute(query, entity_ids)
        rows = cursor.fetchall()
        conn.close()
        
        # Build result dictionary
        result = {}
        for row in rows:
            entity_id, data_json, version = row
            data = json.loads(data_json)
            data['_version'] = version
            result[entity_id] = data
        
        return result
    
    def delete(self, entity_id: str) -> None:
        """Delete entity from database.
        
        Args:
            entity_id: Unique identifier of the entity
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM entities WHERE entity_id = ?", (entity_id,))
        conn.commit()
        conn.close()
    
    def exists(self, entity_id: str) -> bool:
        """Check if entity exists in database.
        
        Args:
            entity_id: Unique identifier of the entity
            
        Returns:
            True if entity exists, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM entities WHERE entity_id = ? LIMIT 1",
            (entity_id,)
        )
        exists = cursor.fetchone() is not None
        conn.close()
        return exists
    
    def list_by_type(self, entity_type: str) -> List[str]:
        """List all entity IDs of a given type.
        
        Args:
            entity_type: Type of entities to list (e.g., 'player', 'mob')
            
        Returns:
            List of entity IDs
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT entity_id FROM entities WHERE entity_type = ?",
            (entity_type,)
        )
        results = [row[0] for row in cursor.fetchall()]
        conn.close()
        return results
    
    def count(self) -> int:
        """Count total number of entities in database.
        
        Returns:
            Number of entities
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM entities")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def clear(self) -> None:
        """Clear all entities from database.
        
        Warning:
            This operation is destructive and cannot be undone.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM entities")
        conn.commit()
        conn.close()
    
    # Referral System Implementation (v0.6.0+)
    
    def get_referral_tree(
        self,
        player_id: str,
        depth: int = 1,
        include_stats: bool = False
    ) -> Dict[str, Any]:
        """Get referral tree for a player.
        
        Args:
            player_id: Root player ID
            depth: How many levels deep to traverse
            include_stats: Whether to include aggregated stats
            
        Returns:
            Dictionary with referral tree structure
        """
        player = self.load(player_id)
        if not player:
            raise ValueError(f"Player {player_id} not found")
        
        # Build tree level by level
        referral_tree = {}
        all_referrals = []
        current_level = [player_id]
        
        for level in range(1, depth + 1):
            next_level = []
            for pid in current_level:
                referrals = self.get_direct_referrals(pid)
                next_level.extend(referrals)
            
            referral_tree[f"level_{level}"] = next_level
            all_referrals.extend(next_level)
            current_level = next_level
            
            if not next_level:
                break  # No more referrals
        
        result = {
            "player_id": player_id,
            "direct_referrals": referral_tree.get("level_1", []),
            "total_referrals": len(all_referrals),
            "referral_tree": referral_tree
        }
        
        # Add stats if requested
        if include_stats:
            stats = self._calculate_referral_stats(all_referrals)
            result["stats"] = stats
        
        return result
    
    def add_referral(
        self,
        referrer_id: str,
        referred_id: str
    ) -> bool:
        """Create a referral link between two players.
        
        Args:
            referrer_id: Player who referred
            referred_id: Player who was referred
            
        Returns:
            True if link created, False if already exists
        """
        # Verify both players exist
        referrer = self.load(referrer_id)
        referred = self.load(referred_id)
        
        if not referrer:
            raise ValueError(f"Referrer {referrer_id} not found")
        if not referred:
            raise ValueError(f"Referred player {referred_id} not found")
        
        # Check if referral already exists
        if referred.get("referrer_id"):
            return False  # Already has a referrer
        
        # Add referrer_id to referred player
        referred["referrer_id"] = referrer_id
        referred["_version"] = referred.get("_version", 1) + 1
        self.save(referred_id, referred)
        
        # Add to referrer's referral list
        if "referrals" not in referrer:
            referrer["referrals"] = []
        
        if referred_id not in referrer["referrals"]:
            referrer["referrals"].append(referred_id)
            referrer["_version"] = referrer.get("_version", 1) + 1
            self.save(referrer_id, referrer)
        
        return True
    
    def get_referrer(self, player_id: str) -> Optional[str]:
        """Get the player who referred this player.
        
        Args:
            player_id: Player to query
            
        Returns:
            Referrer's player ID or None
        """
        player = self.load(player_id)
        if not player:
            return None
        
        return player.get("referrer_id")
    
    def get_direct_referrals(self, player_id: str) -> List[str]:
        """Get list of players directly referred by this player.
        
        Args:
            player_id: Player to query
            
        Returns:
            List of referred player IDs
        """
        player = self.load(player_id)
        if not player:
            return []
        
        return player.get("referrals", [])
    
    def _calculate_referral_stats(self, referral_ids: List[str]) -> Dict[str, Any]:
        """Calculate aggregated stats for a list of referrals.
        
        Args:
            referral_ids: List of referred player IDs
            
        Returns:
            Dictionary with aggregated statistics
        """
        if not referral_ids:
            return {
                "total_spending": 0,
                "active_referrals": 0,
                "total_referrals": 0,
                "average_level": 0
            }
        
        total_spending = 0
        active_count = 0
        total_levels = 0
        
        for player_id in referral_ids:
            player = self.load(player_id)
            if player:
                # Count spending
                total_spending += player.get("total_spent", 0)
                
                # Count active (played in last 7 days, for example)
                if player.get("is_active", False):
                    active_count += 1
                
                # Sum levels
                total_levels += player.get("level", 1)
        
        return {
            "total_spending": total_spending,
            "active_referrals": active_count,
            "total_referrals": len(referral_ids),
            "average_level": total_levels / len(referral_ids) if referral_ids else 0
        }

