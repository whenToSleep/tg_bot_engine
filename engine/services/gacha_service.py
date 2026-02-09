"""Gacha Service - Advanced gacha system with pity mechanics.

This module provides a complete gacha/lootbox system with:
- Rarity tiers (C, B, A, S, SS)
- Soft pity (increasing rates)
- Hard pity (guaranteed drops)
- Multi-pull guarantees
- Pity counter tracking

Designed for CCG games like "Aether Bonds".

Example:
    >>> from engine.services.gacha_service import GachaService, PityConfig
    >>> 
    >>> config = PityConfig(soft_pity_start=70, hard_pity=90, multi_guarantee_rarity="A")
    >>> service = GachaService(config)
    >>> 
    >>> player = {"pity_counter": 0}
    >>> pool = [
    ...     {"id": "card_1", "rarity": "C"},
    ...     {"id": "card_2", "rarity": "S"}
    ... ]
    >>> 
    >>> result = service.single_pull(player, pool)
    >>> print(result.rarity, result.card["id"])
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import random
from engine.core.utils import gacha_pull
from engine.core.unique_entity import create_unique_entity


class RarityTier(Enum):
    """Standard rarity tiers for CCG/Gacha games.
    
    Based on "Aether Bonds" specification:
    - C: Common (70%)
    - B: Rare (20%)
    - A: Epic (8%)
    - S: Legendary (1.5%)
    - SS: Mythic (0.5%)
    """
    C = "C"       # Common
    B = "B"       # Rare
    A = "A"       # Epic
    S = "S"       # Legendary
    SS = "SS"     # Mythic


@dataclass
class PityConfig:
    """Configuration for pity system.
    
    Attributes:
        soft_pity_start: Pull count where soft pity begins (default: 70)
        soft_pity_increment: Rate increase per pull after soft pity (default: 0.05 = 5%)
        hard_pity: Pull count for guaranteed S-rank (default: 90)
        multi_guarantee_rarity: Guaranteed rarity in 10-pull (default: "A")
        multi_pull_size: Size of multi-pull (default: 10)
    
    Example:
        >>> config = PityConfig(soft_pity_start=70, hard_pity=90)
    """
    soft_pity_start: int = 70
    soft_pity_increment: float = 0.05  # 5% per pull
    hard_pity: int = 90
    multi_guarantee_rarity: str = "A"
    multi_pull_size: int = 10


@dataclass
class GachaResult:
    """Result of a gacha pull.
    
    Attributes:
        card: Unique card instance
        rarity: Rarity tier
        was_pity: Whether this was a pity pull
        new_pity_counter: Updated pity counter
    """
    card: Dict[str, Any]
    rarity: str
    was_pity: bool
    new_pity_counter: int


class GachaService:
    """Service for gacha pulls with pity mechanics.
    
    This service handles:
    1. Single pulls with soft/hard pity
    2. Multi-pulls with guaranteed rarity
    3. Pity counter tracking
    4. Rate adjustments based on pity
    
    Example:
        >>> service = GachaService()
        >>> player = {"pity_counter": 75}  # Soft pity active
        >>> pool = get_data_loader().get_all("card")
        >>> result = service.single_pull(player, pool)
        >>> player["pity_counter"] = result.new_pity_counter
    """
    
    # Default rarity weights (Aether Bonds spec)
    DEFAULT_WEIGHTS = {
        "C": 70.0,
        "B": 20.0,
        "A": 8.0,
        "S": 1.5,
        "SS": 0.5
    }
    
    def __init__(self, config: Optional[PityConfig] = None):
        """Initialize gacha service.
        
        Args:
            config: Pity configuration (uses defaults if not provided)
        """
        self.config = config or PityConfig()
    
    def _calculate_adjusted_weights(
        self,
        base_weights: Dict[str, float],
        pity_counter: int
    ) -> Dict[str, float]:
        """Calculate weights adjusted for soft pity.
        
        After soft_pity_start, S-rank rate increases by soft_pity_increment
        for each pull.
        
        Args:
            base_weights: Base rarity weights
            pity_counter: Current pity counter
            
        Returns:
            Adjusted weights
        """
        weights = base_weights.copy()
        
        # Check if soft pity is active
        if pity_counter >= self.config.soft_pity_start:
            pulls_since_soft = pity_counter - self.config.soft_pity_start + 1
            bonus = pulls_since_soft * self.config.soft_pity_increment * 100
            
            # Increase S-rank rate
            weights["S"] += bonus
            
            # Decrease common rate proportionally
            if "C" in weights:
                weights["C"] = max(0, weights["C"] - bonus)
        
        return weights
    
    def single_pull(
        self,
        player: Dict[str, Any],
        pool: List[Dict[str, Any]],
        owner_id: Optional[str] = None,
        rarity_weights: Optional[Dict[str, float]] = None
    ) -> GachaResult:
        """Perform a single gacha pull.
        
        Handles:
        - Soft pity (rate increase)
        - Hard pity (guaranteed S-rank)
        - Pity counter increment/reset
        
        Args:
            player: Player entity (must have "pity_counter" field)
            pool: Card pool to pull from
            owner_id: Optional owner ID for created card
            rarity_weights: Optional custom rarity weights
            
        Returns:
            GachaResult with pulled card and updated pity
            
        Example:
            >>> player = {"pity_counter": 0}
            >>> pool = [{"id": "card_1", "rarity": "C"}, {"id": "card_2", "rarity": "S"}]
            >>> result = service.single_pull(player, pool, owner_id="player_1")
            >>> player["pity_counter"] = result.new_pity_counter
        """
        pity_counter = player.get("pity_counter", 0)
        weights = rarity_weights or self.DEFAULT_WEIGHTS.copy()
        was_pity = False
        
        # Hard pity check
        if pity_counter >= self.config.hard_pity:
            # Guarantee S-rank
            s_cards = [c for c in pool if c.get("rarity") == "S"]
            if s_cards:
                card_template = random.choice(s_cards)
                pity_counter = 0  # Reset pity
                was_pity = True
            else:
                # Fallback if no S-rank cards exist
                card_template = gacha_pull(pool, weights)
        else:
            # Soft pity adjustment
            adjusted_weights = self._calculate_adjusted_weights(weights, pity_counter)
            
            # Normal pull
            card_template = gacha_pull(pool, adjusted_weights)
            
            # Check if S or SS rank was pulled
            rarity = card_template.get("rarity", "C")
            if rarity in ["S", "SS"]:
                pity_counter = 0  # Reset pity
            else:
                pity_counter += 1  # Increment pity
        
        # Create unique instance
        card_instance = create_unique_entity(
            card_template,
            "card",
            owner_id=owner_id or player.get("_id")
        )
        
        return GachaResult(
            card=card_instance,
            rarity=card_instance.get("rarity", "C"),
            was_pity=was_pity,
            new_pity_counter=pity_counter
        )
    
    def multi_pull(
        self,
        player: Dict[str, Any],
        pool: List[Dict[str, Any]],
        owner_id: Optional[str] = None,
        rarity_weights: Optional[Dict[str, float]] = None
    ) -> List[GachaResult]:
        """Perform a multi-pull (10x).
        
        Guarantees:
        - At least one card of multi_guarantee_rarity (default: A)
        - Individual pity still applies to each pull
        
        Args:
            player: Player entity
            pool: Card pool
            owner_id: Optional owner ID
            rarity_weights: Optional custom weights
            
        Returns:
            List of GachaResults (10 cards)
            
        Example:
            >>> player = {"pity_counter": 5}
            >>> results = service.multi_pull(player, pool, owner_id="player_1")
            >>> len(results)
            10
            >>> # At least one A-rank or higher
            >>> any(r.rarity in ["A", "S", "SS"] for r in results)
            True
        """
        results = []
        
        # Perform 10 pulls
        for _ in range(self.config.multi_pull_size):
            result = self.single_pull(player, pool, owner_id, rarity_weights)
            results.append(result)
            
            # Update player's pity counter for next pull
            player["pity_counter"] = result.new_pity_counter
        
        # Check guarantee
        guarantee_met = any(
            self._rarity_rank(r.rarity) >= self._rarity_rank(self.config.multi_guarantee_rarity)
            for r in results
        )
        
        # If guarantee not met, replace worst card with guaranteed rarity
        if not guarantee_met:
            # Find lowest rarity card
            worst_idx = min(
                range(len(results)),
                key=lambda i: self._rarity_rank(results[i].rarity)
            )
            
            # Replace with guaranteed rarity
            guaranteed_cards = [
                c for c in pool
                if c.get("rarity") == self.config.multi_guarantee_rarity
            ]
            
            if guaranteed_cards:
                card_template = random.choice(guaranteed_cards)
                card_instance = create_unique_entity(
                    card_template,
                    "card",
                    owner_id=owner_id or player.get("_id")
                )
                
                results[worst_idx] = GachaResult(
                    card=card_instance,
                    rarity=self.config.multi_guarantee_rarity,
                    was_pity=False,
                    new_pity_counter=results[worst_idx].new_pity_counter
                )
        
        return results
    
    def _rarity_rank(self, rarity: str) -> int:
        """Convert rarity to numeric rank for comparison.
        
        Args:
            rarity: Rarity string (C, B, A, S, SS)
            
        Returns:
            Numeric rank (0-4)
        """
        ranks = {"C": 0, "B": 1, "A": 2, "S": 3, "SS": 4}
        return ranks.get(rarity, 0)
    
    def get_pity_info(self, player: Dict[str, Any]) -> Dict[str, Any]:
        """Get pity status information for player.
        
        Args:
            player: Player entity
            
        Returns:
            Dictionary with pity info
            
        Example:
            >>> player = {"pity_counter": 75}
            >>> info = service.get_pity_info(player)
            >>> info["soft_pity_active"]
            True
            >>> info["pulls_until_hard_pity"]
            15
        """
        pity_counter = player.get("pity_counter", 0)
        
        return {
            "pity_counter": pity_counter,
            "soft_pity_active": pity_counter >= self.config.soft_pity_start,
            "pulls_until_hard_pity": max(0, self.config.hard_pity - pity_counter),
            "current_s_rate": self._calculate_adjusted_weights(
                self.DEFAULT_WEIGHTS, pity_counter
            ).get("S", 1.5)
        }


def create_gacha_service(config: Optional[Dict[str, Any]] = None) -> GachaService:
    """Factory function to create a GachaService.
    
    Args:
        config: Optional configuration dict
        
    Returns:
        GachaService instance
        
    Example:
        >>> service = create_gacha_service({
        ...     "soft_pity_start": 70,
        ...     "hard_pity": 90
        ... })
    """
    if config:
        pity_config = PityConfig(**config)
        return GachaService(pity_config)
    return GachaService()

