"""Progression module - Player leveling and experience.

This module tracks player experience and handles leveling up.
Subscribes to mob kill events to grant experience.
"""

from typing import Dict, Any
from engine.core.state import GameState
from engine.core.events import (
    Event,
    get_event_bus,
    MobKilledEvent,
    PlayerLevelUpEvent
)
from engine.core.data_loader import get_global_loader


class ProgressionModule:
    """Module for player progression (experience and levels).
    
    Listens to mob kill events and grants experience based on mob data.
    Automatically handles level ups and stat increases.
    
    Example:
        >>> state = GameState()
        >>> module = ProgressionModule(state)
        >>> # Module listens to mob_killed events
        >>> # Grants exp and handles levelups automatically
    """
    
    def __init__(self, state: GameState) -> None:
        """Initialize progression module.
        
        Args:
            state: Game state to operate on
        """
        self.state = state
        
        # Subscribe to events
        event_bus = get_event_bus()
        event_bus.subscribe("mob_killed", self.on_mob_killed)
    
    def on_mob_killed(self, event: Event) -> None:
        """Handle mob killed event.
        
        Args:
            event: MobKilledEvent with kill data
        """
        player_id = event.data["player_id"]
        mob_template = event.data["mob_template"]
        
        # Get player
        player = self.state.get_entity(player_id)
        if player is None:
            return
        
        # Get exp reward from mob data
        exp_reward = self._get_exp_reward(mob_template)
        
        # Grant exp
        self._grant_exp(player, player_id, exp_reward)
        
        # Save player
        self.state.set_entity(player_id, player)
    
    def _get_exp_reward(self, mob_template: str) -> int:
        """Get experience reward for killing mob.
        
        Args:
            mob_template: Mob template ID
            
        Returns:
            Experience points to grant
        """
        loader = get_global_loader()
        
        # Load mobs if not loaded
        if not loader.is_loaded("mobs"):
            try:
                loader.load_category("mobs", "mob_schema.json")
            except Exception:
                return 10  # Default exp
        
        # Get mob data
        mob_data = loader.get("mobs", mob_template)
        if mob_data is None:
            return 10  # Default exp
        
        return mob_data.get("experience_reward", 10)
    
    def _grant_exp(
        self,
        player: Dict[str, Any],
        player_id: str,
        exp_amount: int
    ) -> None:
        """Grant experience to player and check for levelup.
        
        Args:
            player: Player data
            player_id: Player ID
            exp_amount: Experience to grant
        """
        # Initialize level/exp if not present
        if "level" not in player:
            player["level"] = 1
        if "exp" not in player:
            player["exp"] = 0
        
        current_level = player["level"]
        current_exp = player["exp"]
        
        # Add exp
        new_exp = current_exp + exp_amount
        player["exp"] = new_exp
        
        # Check for levelup
        exp_needed = self._exp_for_next_level(current_level)
        
        while player["exp"] >= exp_needed:
            # Level up!
            old_level = player["level"]
            player["level"] += 1
            player["exp"] -= exp_needed
            
            # Grant stat increases
            self._grant_levelup_stats(player)
            
            # Publish levelup event
            event_bus = get_event_bus()
            event_bus.publish(PlayerLevelUpEvent(
                player_id=player_id,
                old_level=old_level,
                new_level=player["level"]
            ))
            
            # Recalculate exp needed for next level
            exp_needed = self._exp_for_next_level(player["level"])
    
    def _exp_for_next_level(self, current_level: int) -> int:
        """Calculate experience needed for next level.
        
        Args:
            current_level: Current player level
            
        Returns:
            Experience points needed to reach next level
            
        Note:
            Formula: level * 100 (simple linear scaling)
            Level 1 -> 2: 100 exp
            Level 2 -> 3: 200 exp
            Level 10 -> 11: 1000 exp
        """
        return current_level * 100
    
    def _grant_levelup_stats(self, player: Dict[str, Any]) -> None:
        """Grant stat increases on levelup.
        
        Args:
            player: Player data to modify
            
        Note:
            Grants:
            - +10 HP per level
            - +2 Attack per level
            - +1 Defense per level
        """
        # Initialize stats if not present
        if "max_hp" not in player:
            player["max_hp"] = 100
        if "hp" not in player:
            player["hp"] = player["max_hp"]
        if "attack" not in player:
            player["attack"] = 10
        if "defense" not in player:
            player["defense"] = 0
        
        # Grant stat increases
        player["max_hp"] += 10
        player["hp"] = player["max_hp"]  # Full heal on levelup
        player["attack"] += 2
        player["defense"] += 1

