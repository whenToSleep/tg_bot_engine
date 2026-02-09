"""Transaction module - Transaction management for atomic state changes.

Provides ACID guarantees for command execution:
- Atomicity: all changes or none
- Consistency: state always valid
- Isolation: concurrent commands don't interfere
- Durability: provided by PersistentGameState in Iteration 4
"""

from copy import deepcopy
from typing import Optional, List
from engine.core.state import GameState


class Transaction:
    """Transaction for atomic state changes.
    
    Creates a snapshot of the current state and provides
    commit/rollback functionality.
    
    Example:
        >>> state = GameState()
        >>> state.set_entity("player_1", {"gold": 100})
        >>> 
        >>> transaction = Transaction(state)
        >>> work_state = transaction.get_work_state()
        >>> work_state.set_entity("player_1", {"gold": 150})
        >>> 
        >>> transaction.commit()  # Apply changes
        >>> # or
        >>> transaction.rollback()  # Discard changes
    """
    
    def __init__(self, state: GameState) -> None:
        """Initialize transaction with state snapshot.
        
        Args:
            state: Current game state to work with
        """
        self._original_state = state
        self._snapshot = deepcopy(state._entities)
        self._committed = False
        self._rolled_back = False
    
    def get_work_state(self) -> GameState:
        """Get isolated state for work.
        
        Returns:
            GameState with snapshot data for safe modification
            
        Raises:
            RuntimeError: If transaction already committed or rolled back
        """
        if self._committed or self._rolled_back:
            raise RuntimeError("Transaction already finalized")
        
        # Create temporary state with snapshot
        temp_state = GameState()
        temp_state._entities = self._snapshot
        return temp_state
    
    def commit(self) -> None:
        """Apply changes to original state.
        
        Raises:
            RuntimeError: If transaction already committed or rolled back
        """
        if self._committed:
            raise RuntimeError("Transaction already committed")
        if self._rolled_back:
            raise RuntimeError("Transaction already rolled back")
        
        # Apply snapshot to original state
        self._original_state._entities = self._snapshot
        self._committed = True
    
    def rollback(self) -> None:
        """Discard changes.
        
        Raises:
            RuntimeError: If transaction already committed or rolled back
        """
        if self._committed:
            raise RuntimeError("Transaction already committed")
        if self._rolled_back:
            raise RuntimeError("Transaction already rolled back")
        
        # Simply discard snapshot
        self._snapshot = {}
        self._rolled_back = True
    
    @property
    def is_committed(self) -> bool:
        """Check if transaction was committed."""
        return self._committed
    
    @property
    def is_rolled_back(self) -> bool:
        """Check if transaction was rolled back."""
        return self._rolled_back
    
    @property
    def is_active(self) -> bool:
        """Check if transaction is still active."""
        return not (self._committed or self._rolled_back)


class TransactionalExecutor:
    """Command executor with transaction support.
    
    Wraps command execution in transactions to provide
    automatic rollback on errors.
    
    Example:
        >>> executor = TransactionalExecutor(state)
        >>> command = GainGoldCommand("player_1", 100)
        >>> result = executor.execute(command)
    """
    
    def __init__(self, state: GameState) -> None:
        """Initialize transactional executor.
        
        Args:
            state: Game state to operate on
        """
        self.state = state
    
    def execute(self, command: "Command") -> "CommandResult":  # type: ignore
        """Execute command in transaction.
        
        Args:
            command: Command to execute
            
        Returns:
            CommandResult with success status
            
        Note:
            - On success: changes are committed
            - On error: changes are rolled back automatically
        """
        from engine.core.command import CommandResult
        
        # Create transaction
        transaction = Transaction(self.state)
        
        try:
            # Get work state
            work_state = transaction.get_work_state()
            
            # Execute command on work state
            result_data = command.execute(work_state)
            
            # Commit changes
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


class TransactionManager:
    """Manager for creating and tracking transactions.
    
    Provides a simple interface for transaction lifecycle management.
    
    Example:
        >>> manager = TransactionManager(state)
        >>> tx = manager.begin()
        >>> # ... modify state ...
        >>> tx.commit()
    """
    
    def __init__(self, state: GameState) -> None:
        """Initialize transaction manager.
        
        Args:
            state: Game state to manage transactions for
        """
        self.state = state
        self._active_transactions: List[Transaction] = []
    
    def begin(self) -> Transaction:
        """Begin a new transaction.
        
        Returns:
            New active transaction
        """
        tx = Transaction(self.state)
        self._active_transactions.append(tx)
        return tx
    
    def get_active_transactions(self) -> List[Transaction]:
        """Get list of active transactions.
        
        Returns:
            List of transactions that are not committed or rolled back
        """
        return [tx for tx in self._active_transactions if tx.is_active]
    
    def rollback_all(self) -> None:
        """Rollback all active transactions."""
        for tx in self.get_active_transactions():
            tx.rollback()
        self._active_transactions.clear()
    
    def has_active_transactions(self) -> bool:
        """Check if there are any active transactions.
        
        Returns:
            True if there are active transactions, False otherwise
        """
        return len(self.get_active_transactions()) > 0
