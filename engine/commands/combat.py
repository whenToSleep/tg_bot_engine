"""Combat commands - Battle mechanics.

This module provides commands for combat:
- AttackMobCommand: Player attacks a mob

Combat now supports stat modifiers (buffs/debuffs) via engine.core.modifiers.
"""

from typing import Any
from engine.core.command import Command
from engine.core.state import GameState
from engine.core.events import get_event_bus, MobKilledEvent, GoldChangedEvent
from engine.core.modifiers import StatCalculator


class AttackMobCommand(Command):
    """Command for player to attack a mob.
    
    Simple combat mechanics:
    - Player deals damage equal to their 'attack' stat
    - Mob HP is reduced
    - If mob dies (HP <= 0), player gains gold reward
    
    Example:
        >>> cmd = AttackMobCommand("player_1", "mob_1")
        >>> result = executor.execute(cmd, state)
        >>> print(result.data['mob_killed'])
        True
    """
    
    def __init__(self, player_id: str, mob_id: str) -> None:
        """Initialize AttackMobCommand.
        
        Args:
            player_id: Unique identifier of the player
            mob_id: Unique identifier of the mob to attack
        """
        self.player_id = player_id
        self.mob_id = mob_id
    
    def get_entity_dependencies(self) -> list[str]:
        """Get entity dependencies.
        
        Note:
            Returns sorted list to ensure consistent lock ordering.
        """
        return sorted([self.player_id, self.mob_id])
    
    def execute(self, state: GameState) -> dict[str, Any]:
        """Execute the attack command.
        
        Args:
            state: Current game state
            
        Returns:
            Dictionary with:
                - damage_dealt: Damage dealt to mob
                - mob_hp: Remaining mob HP
                - mob_killed: Whether mob was killed
                - gold_gained: Gold gained (if mob killed, else 0)
            
        Raises:
            KeyError: If player or mob doesn't exist
        """
        # Get player
        player = state.get_entity(self.player_id)
        if player is None:
            raise KeyError(f"Player {self.player_id} does not exist")
        
        # Get mob
        mob = state.get_entity(self.mob_id)
        if mob is None:
            raise KeyError(f"Mob {self.mob_id} does not exist")
        
        # Calculate damage with modifiers applied
        player_stats = StatCalculator.get_all_stats(player)
        damage = int(player_stats.get("attack", 10))
        
        # Deal damage to mob
        mob_hp = mob.get("hp", 100)
        mob_hp -= damage
        mob["hp"] = mob_hp
        
        # Check if mob is killed
        mob_killed = mob_hp <= 0
        gold_gained = 0
        
        if mob_killed:
            # Mob is dead, give gold reward
            gold_reward = mob.get("gold_reward", 0)
            player_gold = player.get("gold", 0)
            player["gold"] = player_gold + gold_reward
            gold_gained = gold_reward
            
            # Update player first (before events)
            state.set_entity(self.player_id, player)
            
            # Remove mob from state
            state.delete_entity(self.mob_id)
            
            # Publish MobKilledEvent
            event_bus = get_event_bus()
            event_bus.publish(MobKilledEvent(
                player_id=self.player_id,
                mob_id=self.mob_id,
                mob_template=mob.get("_template_id", "unknown"),
                damage_dealt=damage
            ))
            
            # Publish GoldChangedEvent if gold was gained
            if gold_gained > 0:
                event_bus.publish(GoldChangedEvent(
                    player_id=self.player_id,
                    old_gold=player_gold,
                    new_gold=player_gold + gold_gained,
                    change=gold_gained,
                    reason="mob_kill_reward"
                ))
        else:
            # Mob still alive, update its HP
            state.set_entity(self.mob_id, mob)
            # Update player
            state.set_entity(self.player_id, player)
        
        return {
            "damage_dealt": damage,
            "mob_hp": max(0, mob_hp),  # Don't show negative HP
            "mob_killed": mob_killed,
            "gold_gained": gold_gained,
        }

