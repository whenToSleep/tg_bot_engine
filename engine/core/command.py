"""Command module - Base classes for command pattern implementation.

Commands are atomic operations that modify game state.
They are deterministic, testable, and form the core of the game engine.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class CommandResult:
    """Result of command execution.
    
    Attributes:
        success: Whether the command executed successfully
        data: Result data (when successful)
        error: Error message (when failed)
    """
    success: bool
    data: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    
    @classmethod
    def success_result(cls, data: dict[str, Any]) -> "CommandResult":
        """Create a successful result."""
        return cls(success=True, data=data, error=None)
    
    @classmethod
    def error_result(cls, error: str) -> "CommandResult":
        """Create an error result."""
        return cls(success=False, data=None, error=error)


class Command(ABC):
    """Base class for all game commands.
    
    Commands are atomic operations that modify game state.
    They must be:
    - Deterministic: same input → same output
    - Atomic: either fully executed or not at all
    - Testable: can be tested without external dependencies
    
    Example:
        >>> class GainGoldCommand(Command):
        ...     def __init__(self, player_id: str, amount: int):
        ...         self.player_id = player_id
        ...         self.amount = amount
        ...     
        ...     def get_entity_dependencies(self) -> list[str]:
        ...         return [self.player_id]
        ...     
        ...     def execute(self, state: GameState) -> dict:
        ...         player = state.get_entity(self.player_id)
        ...         player['gold'] = player.get('gold', 0) + self.amount
        ...         state.set_entity(self.player_id, player)
        ...         return {"new_gold": player['gold']}
    """
    
    def get_entity_dependencies(self) -> list[str]:
        """Get list of entity IDs this command will access.
        
        Returns:
            List of entity IDs that will be read or modified
            
        Note:
            - Used for entity locking in concurrent execution
            - Must include ALL entities the command touches
            - Default implementation returns empty list (no locking)
        """
        return []
    
    @abstractmethod
    def execute(self, state: "GameState") -> dict[str, Any]:  # type: ignore
        """Execute the command on the given game state.
        
        Args:
            state: Current game state to modify
            
        Returns:
            Dictionary with result data
            
        Raises:
            ValueError: When command cannot be executed (validation failed)
            KeyError: When required entity not found
            
        Note:
            - This method should be pure (no side effects except state modification)
            - Raise exceptions for validation errors (triggers rollback)
            - Return dict with result data on success
        """
        raise NotImplementedError("Subclasses must implement execute()")

