"""Async executor module - Asynchronous command execution with locking.

Provides async command execution with entity locking and transactions
to prevent race conditions and ensure data consistency.
"""

import asyncio
from engine.core.command import Command, CommandResult
from engine.core.state import GameState
from engine.core.transaction import Transaction
from engine.core.locks import EntityLockManager


class AsyncCommandExecutor:
    """Asynchronous command executor with entity locking.
    
    Combines transactions and entity locking to provide:
    - ACID guarantees through transactions
    - Race condition prevention through entity locks
    - Deadlock prevention through sorted locking
    
    Example:
        >>> executor = AsyncCommandExecutor(state)
        >>> result = await executor.execute(command)
    """
    
    def __init__(self, state: GameState) -> None:
        """Initialize async executor.
        
        Args:
            state: Game state to operate on
        """
        self.state = state
        self.lock_manager = EntityLockManager()
    
    async def execute(self, command: Command) -> CommandResult:
        """Execute command asynchronously with locking.
        
        Args:
            command: Command to execute
            
        Returns:
            CommandResult with success status and data
            
        Note:
            Process:
            1. Get entity dependencies from command
            2. Acquire locks for entities (sorted to prevent deadlock)
            3. Create transaction
            4. Execute command in transaction
            5. Commit or rollback
            6. Release locks
        """
        # Get entity dependencies
        entity_ids = command.get_entity_dependencies()
        
        # Acquire locks for all entities
        async with self.lock_manager.lock_entities(entity_ids):
            # Create transaction
            transaction = Transaction(self.state)
            
            try:
                # Get work state from transaction
                work_state = transaction.get_work_state()
                
                # Execute command (synchronous call)
                result_data = command.execute(work_state)
                
                # Commit transaction
                transaction.commit()
                
                return CommandResult.success_result(result_data)
                
            except ValueError as e:
                # Validation error - rollback
                transaction.rollback()
                return CommandResult.error_result(f"Validation error: {str(e)}")
                
            except KeyError as e:
                # Entity not found - rollback
                transaction.rollback()
                return CommandResult.error_result(f"Entity not found: {str(e)}")
                
            except Exception as e:
                # Unexpected error - rollback
                transaction.rollback()
                return CommandResult.error_result(
                    f"Unexpected error: {type(e).__name__}: {str(e)}"
                )
    
    async def execute_batch(self, commands: list[Command]) -> list[CommandResult]:
        """Execute multiple commands in parallel.
        
        Args:
            commands: List of commands to execute
            
        Returns:
            List of CommandResults
            
        Note:
            Commands are executed in parallel where possible.
            Conflicting commands (same entities) are serialized automatically.
        """
        tasks = [self.execute(cmd) for cmd in commands]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error results
        final_results = []
        for result in results:
            if isinstance(result, Exception):
                final_results.append(
                    CommandResult.error_result(f"Execution failed: {str(result)}")
                )
            else:
                final_results.append(result)
        
        return final_results
    
    def get_lock_stats(self) -> dict:
        """Get locking statistics.
        
        Returns:
            Dictionary with lock statistics
        """
        return {
            "total_locks": len(self.lock_manager._locks),
            "locked_entities": sum(
                1 for lock in self.lock_manager._locks.values() if lock.locked()
            ),
        }

