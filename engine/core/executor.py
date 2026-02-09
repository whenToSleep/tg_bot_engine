"""Executor module - Command execution engine.

CommandExecutor handles the execution of commands and
provides error handling with automatic rollback on failure.
"""

from engine.core.command import Command, CommandResult
from engine.core.state import GameState


class CommandExecutor:
    """Command execution engine.
    
    Executes commands on game state with error handling.
    In Iteration 0, this is a simple executor.
    Future iterations will add:
    - Transaction support (commit/rollback)
    - Entity locking (concurrency control)
    - Event publishing
    
    Example:
        >>> state = GameState()
        >>> executor = CommandExecutor()
        >>> command = GainGoldCommand("player_1", 100)
        >>> result = executor.execute(command, state)
        >>> print(result.success)
        True
    """
    
    def __init__(self) -> None:
        """Initialize command executor."""
        pass
    
    def execute(self, command: Command, state: GameState) -> CommandResult:
        """Execute a command on the given state.
        
        Args:
            command: Command to execute
            state: Game state to operate on
            
        Returns:
            CommandResult with success status and data/error
            
        Note:
            - Exceptions raised by command are caught and returned as error result
            - State modifications are NOT rolled back in Iteration 0
              (Transaction support will be added in Iteration 1)
        """
        try:
            # Execute command and get result data
            result_data = command.execute(state)
            
            # Return success result
            return CommandResult.success_result(result_data)
            
        except ValueError as e:
            # Validation errors (e.g., insufficient gold)
            return CommandResult.error_result(f"Validation error: {str(e)}")
            
        except KeyError as e:
            # Entity not found errors
            return CommandResult.error_result(f"Entity not found: {str(e)}")
            
        except Exception as e:
            # Unexpected errors
            return CommandResult.error_result(f"Unexpected error: {type(e).__name__}: {str(e)}")

