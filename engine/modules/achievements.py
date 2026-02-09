"""Achievement module - Track and reward player achievements.

This module listens to game events and updates player achievements.
Completely decoupled from combat/economy systems.
"""

from typing import Dict, Any
from engine.core.state import GameState
from engine.core.events import (
    Event,
    get_event_bus,
    MobKilledEvent,
    AchievementUnlockedEvent,
    GoldChangedEvent
)


class AchievementModule:
    """Module for tracking player achievements.
    
    Subscribes to game events and tracks progress towards achievements.
    When achievement is unlocked, publishes AchievementUnlockedEvent and
    grants rewards.
    
    Example:
        >>> state = GameState()
        >>> module = AchievementModule(state)
        >>> # Module now listens to events
        >>> # When MobKilledEvent is published, module updates progress
    """
    
    def __init__(self, state: GameState) -> None:
        """Initialize achievement module.
        
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
            event: MobKilledEvent with mob kill data
        """
        player_id = event.data["player_id"]
        mob_template = event.data["mob_template"]
        
        # Get player
        player = self.state.get_entity(player_id)
        if player is None:
            return  # Player doesn't exist
        
        # Initialize achievements if not present
        if "achievements" not in player:
            player["achievements"] = {}
        
        if "achievement_progress" not in player:
            player["achievement_progress"] = {}
        
        # Check for achievements related to this mob type
        self._check_goblin_slayer(player, player_id, mob_template)
        self._check_orc_hunter(player, player_id, mob_template)
        self._check_dragon_slayer(player, player_id, mob_template)
        self._check_monster_hunter(player, player_id, mob_template)
        
        # Save player
        self.state.set_entity(player_id, player)
    
    def _check_goblin_slayer(
        self,
        player: Dict[str, Any],
        player_id: str,
        mob_template: str
    ) -> None:
        """Check Goblin Slayer achievement (Kill 10 goblins)."""
        if mob_template == "goblin_warrior":
            achievement_id = "goblin_slayer"
            
            # Already unlocked?
            if achievement_id in player["achievements"]:
                return
            
            # Increment progress
            progress = player["achievement_progress"].get(achievement_id, 0) + 1
            player["achievement_progress"][achievement_id] = progress
            
            # Check if unlocked
            if progress >= 10:
                self._unlock_achievement(
                    player,
                    player_id,
                    achievement_id,
                    "Goblin Slayer",
                    gold_reward=1000
                )
    
    def _check_orc_hunter(
        self,
        player: Dict[str, Any],
        player_id: str,
        mob_template: str
    ) -> None:
        """Check Orc Hunter achievement (Kill 5 orcs)."""
        if mob_template == "orc_chieftain":
            achievement_id = "orc_hunter"
            
            if achievement_id in player["achievements"]:
                return
            
            progress = player["achievement_progress"].get(achievement_id, 0) + 1
            player["achievement_progress"][achievement_id] = progress
            
            if progress >= 5:
                self._unlock_achievement(
                    player,
                    player_id,
                    achievement_id,
                    "Orc Hunter",
                    gold_reward=2500
                )
    
    def _check_dragon_slayer(
        self,
        player: Dict[str, Any],
        player_id: str,
        mob_template: str
    ) -> None:
        """Check Dragon Slayer achievement (Kill 1 dragon)."""
        if mob_template == "dragon_ancient":
            achievement_id = "dragon_slayer"
            
            if achievement_id in player["achievements"]:
                return
            
            # Dragon slayer is instant (1 kill)
            self._unlock_achievement(
                player,
                player_id,
                achievement_id,
                "Dragon Slayer",
                gold_reward=10000
            )
    
    def _check_monster_hunter(
        self,
        player: Dict[str, Any],
        player_id: str,
        mob_template: str
    ) -> None:
        """Check Monster Hunter achievement (Kill 50 monsters total)."""
        achievement_id = "monster_hunter"
        
        if achievement_id in player["achievements"]:
            return
        
        # Count all mob kills
        progress = player["achievement_progress"].get(achievement_id, 0) + 1
        player["achievement_progress"][achievement_id] = progress
        
        if progress >= 50:
            self._unlock_achievement(
                player,
                player_id,
                achievement_id,
                "Monster Hunter",
                gold_reward=5000
            )
    
    def _unlock_achievement(
        self,
        player: Dict[str, Any],
        player_id: str,
        achievement_id: str,
        achievement_name: str,
        gold_reward: int = 0
    ) -> None:
        """Unlock achievement and grant rewards.
        
        Args:
            player: Player data
            player_id: Player ID
            achievement_id: Achievement identifier
            achievement_name: Display name
            gold_reward: Gold reward to grant
        """
        # Mark as unlocked
        player["achievements"][achievement_id] = {
            "name": achievement_name,
            "unlocked": True
        }
        
        # Grant gold reward
        if gold_reward > 0:
            old_gold = player.get("gold", 0)
            player["gold"] = old_gold + gold_reward
            
            # Publish gold changed event
            event_bus = get_event_bus()
            event_bus.publish(GoldChangedEvent(
                player_id=player_id,
                old_gold=old_gold,
                new_gold=old_gold + gold_reward,
                change=gold_reward,
                reason=f"achievement_{achievement_id}"
            ))
        
        # Publish achievement unlocked event
        event_bus = get_event_bus()
        event_bus.publish(AchievementUnlockedEvent(
            player_id=player_id,
            achievement_id=achievement_id,
            achievement_name=achievement_name
        ))

