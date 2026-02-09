"""Economy commands - Gold and resource management.

This module provides commands for managing in-game economy:
- GainGoldCommand: Add gold to player
- SpendGoldCommand: Remove gold from player (with validation)
"""

from typing import Any
from engine.core.command import Command
from engine.core.state import GameState


class GainGoldCommand(Command):
    """Command to add gold to a player.
    
    This command always succeeds if the player exists.
    If player doesn't exist, it will be created with the given gold amount.
    
    Example:
        >>> cmd = GainGoldCommand("player_1", 100)
        >>> result = executor.execute(cmd, state)
        >>> print(result.data['new_gold'])
        100
    """
    
    def __init__(self, player_id: str, amount: int) -> None:
        """Initialize GainGoldCommand.
        
        Args:
            player_id: Unique identifier of the player
            amount: Amount of gold to add (can be negative for debugging)
        """
        self.player_id = player_id
        self.amount = amount
    
    def get_entity_dependencies(self) -> list[str]:
        """Get entity dependencies."""
        return [self.player_id]
    
    def execute(self, state: GameState) -> dict[str, Any]:
        """Execute the command to add gold.
        
        Args:
            state: Current game state
            
        Returns:
            Dictionary with 'new_gold' key containing updated gold amount
        """
        # Get player or create new one
        player = state.get_entity(self.player_id)
        if player is None:
            player = {"gold": 0}
        
        # Add gold
        current_gold = player.get("gold", 0)
        new_gold = current_gold + self.amount
        player["gold"] = new_gold
        
        # Save player
        state.set_entity(self.player_id, player)
        
        return {"new_gold": new_gold}


class SpendGoldCommand(Command):
    """Command to spend gold from a player.
    
    This command validates that the player has enough gold.
    Raises ValueError if insufficient funds.
    
    Example:
        >>> cmd = SpendGoldCommand("player_1", 50)
        >>> result = executor.execute(cmd, state)
        >>> if result.success:
        ...     print(f"Gold remaining: {result.data['new_gold']}")
    """
    
    def __init__(self, player_id: str, amount: int) -> None:
        """Initialize SpendGoldCommand.
        
        Args:
            player_id: Unique identifier of the player
            amount: Amount of gold to spend (must be positive)
        """
        self.player_id = player_id
        self.amount = amount
    
    def get_entity_dependencies(self) -> list[str]:
        """Get entity dependencies."""
        return [self.player_id]
    
    def execute(self, state: GameState) -> dict[str, Any]:
        """Execute the command to spend gold.
        
        Args:
            state: Current game state
            
        Returns:
            Dictionary with 'new_gold' key containing updated gold amount
            
        Raises:
            ValueError: If player doesn't have enough gold
            KeyError: If player doesn't exist
        """
        # Get player (must exist)
        player = state.get_entity(self.player_id)
        if player is None:
            raise KeyError(f"Player {self.player_id} does not exist")
        
        # Check if player has enough gold
        current_gold = player.get("gold", 0)
        if current_gold < self.amount:
            raise ValueError(
                f"Not enough gold: has {current_gold}, needs {self.amount}"
            )
        
        # Spend gold
        new_gold = current_gold - self.amount
        player["gold"] = new_gold
        
        # Save player
        state.set_entity(self.player_id, player)
        
        return {"new_gold": new_gold}

