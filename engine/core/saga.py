"""Saga Pattern - Complex multi-step transactions with compensating actions.

This module implements the Saga pattern for distributed transactions:
- Multi-step operations (prepare → execute → commit)
- Compensating actions for rollback
- Automatic compensation on failure
- Step-by-step execution with checkpoints

Designed for complex operations like card fusion, trades, auctions.

Example:
    >>> from engine.core.saga import Saga, SagaStep
    >>> 
    >>> # Define saga steps
    >>> saga = Saga("card_fusion")
    >>> 
    >>> # Step 1: Remove source cards
    >>> saga.add_step(
    ...     name="remove_cards",
    ...     action=lambda state: remove_cards(state, ["card_1", "card_2"]),
    ...     compensation=lambda state: restore_cards(state, ["card_1", "card_2"])
    ... )
    >>> 
    >>> # Step 2: Create fused card
    >>> saga.add_step(
    ...     name="create_fused",
    ...     action=lambda state: create_card(state, "fused_card"),
    ...     compensation=lambda state: delete_card(state, "fused_card")
    ... )
    >>> 
    >>> # Execute saga
    >>> result = saga.execute(state)
    >>> if not result.success:
    ...     # Automatic compensation already performed
    ...     print(f"Saga failed: {result.message}")
"""

from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass, field
from enum import Enum
from engine.core.state import GameState
from engine.core.command import CommandResult
import logging

logger = logging.getLogger(__name__)


class SagaStatus(str, Enum):
    """Status of a saga execution."""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    COMPENSATING = "compensating"
    FAILED = "failed"


@dataclass
class SagaStep:
    """A single step in a saga.
    
    Attributes:
        name: Step name for logging
        action: Function to execute (state) -> Any
        compensation: Optional function to undo action (state) -> None
        executed: Whether this step has been executed
        compensated: Whether compensation has been applied
    """
    name: str
    action: Callable[[GameState], Any]
    compensation: Optional[Callable[[GameState], None]] = None
    executed: bool = False
    compensated: bool = False
    result: Any = None


@dataclass
class SagaExecutionContext:
    """Context for saga execution.
    
    Tracks execution state and results.
    """
    saga_id: str
    status: SagaStatus = SagaStatus.PENDING
    completed_steps: List[str] = field(default_factory=list)
    failed_step: Optional[str] = None
    error_message: Optional[str] = None
    results: Dict[str, Any] = field(default_factory=dict)


class Saga:
    """Saga orchestrator for complex multi-step transactions.
    
    Implements the Saga pattern:
    1. Execute steps sequentially
    2. If any step fails, execute compensating actions in reverse order
    3. Guarantee atomicity across multiple operations
    
    Features:
    - Step-by-step execution with checkpoints
    - Automatic compensation on failure
    - Detailed logging for debugging
    - Results aggregation
    
    Example:
        >>> saga = Saga("player_trade")
        >>> 
        >>> # Step 1: Lock player 1's items
        >>> saga.add_step(
        ...     "lock_p1_items",
        ...     action=lambda s: lock_items(s, "p1", ["sword"]),
        ...     compensation=lambda s: unlock_items(s, "p1", ["sword"])
        ... )
        >>> 
        >>> # Step 2: Lock player 2's items
        >>> saga.add_step(
        ...     "lock_p2_items",
        ...     action=lambda s: lock_items(s, "p2", ["gold_100"]),
        ...     compensation=lambda s: unlock_items(s, "p2", ["gold_100"])
        ... )
        >>> 
        >>> # Step 3: Transfer items
        >>> saga.add_step(
        ...     "transfer_items",
        ...     action=lambda s: transfer_all(s, "p1", "p2", ["sword"], ["gold_100"]),
        ...     compensation=lambda s: transfer_all(s, "p2", "p1", ["sword"], ["gold_100"])
        ... )
        >>> 
        >>> result = saga.execute(state)
    """
    
    def __init__(self, saga_id: str):
        """Initialize saga.
        
        Args:
            saga_id: Unique identifier for this saga
        """
        self.saga_id = saga_id
        self.steps: List[SagaStep] = []
        self.context = SagaExecutionContext(saga_id=saga_id)
    
    def add_step(
        self,
        name: str,
        action: Callable[[GameState], Any],
        compensation: Optional[Callable[[GameState], None]] = None
    ) -> "Saga":
        """Add a step to the saga.
        
        Args:
            name: Step name for logging
            action: Function to execute
            compensation: Optional compensation function
            
        Returns:
            Self for chaining
        """
        step = SagaStep(
            name=name,
            action=action,
            compensation=compensation
        )
        self.steps.append(step)
        return self
    
    def execute(self, state: GameState) -> CommandResult:
        """Execute the saga.
        
        Args:
            state: Game state to operate on
            
        Returns:
            CommandResult with success status
        """
        self.context.status = SagaStatus.EXECUTING
        logger.info(f"Saga '{self.saga_id}' started ({len(self.steps)} steps)")
        
        # Execute steps sequentially
        for i, step in enumerate(self.steps):
            try:
                logger.debug(f"Saga '{self.saga_id}' - Step {i+1}/{len(self.steps)}: {step.name}")
                
                # Execute step action
                result = step.action(state)
                step.executed = True
                step.result = result
                
                # Record completion
                self.context.completed_steps.append(step.name)
                self.context.results[step.name] = result
                
                logger.debug(f"Saga '{self.saga_id}' - Step '{step.name}' completed")
                
            except Exception as e:
                # Step failed - initiate compensation
                logger.error(f"Saga '{self.saga_id}' - Step '{step.name}' failed: {e}")
                
                self.context.status = SagaStatus.COMPENSATING
                self.context.failed_step = step.name
                self.context.error_message = str(e)
                
                # Compensate all executed steps in reverse order
                compensation_success = self._compensate(state)
                
                if compensation_success:
                    self.context.status = SagaStatus.FAILED
                    return CommandResult(
                        success=False,
                        message=f"Saga '{self.saga_id}' failed at step '{step.name}': {e}. Compensation completed.",
                        metadata={
                            "saga_id": self.saga_id,
                            "failed_step": step.name,
                            "completed_steps": self.context.completed_steps,
                            "compensated": True
                        }
                    )
                else:
                    # Compensation failed - critical error
                    self.context.status = SagaStatus.FAILED
                    return CommandResult(
                        success=False,
                        message=f"Saga '{self.saga_id}' failed at step '{step.name}': {e}. CRITICAL: Compensation also failed!",
                        metadata={
                            "saga_id": self.saga_id,
                            "failed_step": step.name,
                            "completed_steps": self.context.completed_steps,
                            "compensated": False,
                            "critical_error": True
                        }
                    )
        
        # All steps completed successfully
        self.context.status = SagaStatus.COMPLETED
        logger.info(f"Saga '{self.saga_id}' completed successfully")
        
        return CommandResult(
            success=True,
            message=f"Saga '{self.saga_id}' completed successfully",
            metadata={
                "saga_id": self.saga_id,
                "completed_steps": self.context.completed_steps,
                "results": self.context.results
            }
        )
    
    def _compensate(self, state: GameState) -> bool:
        """Execute compensating actions in reverse order.
        
        Args:
            state: Game state
            
        Returns:
            True if all compensations succeeded, False otherwise
        """
        logger.info(f"Saga '{self.saga_id}' - Starting compensation")
        
        # Get executed steps in reverse order
        executed_steps = [step for step in self.steps if step.executed]
        executed_steps.reverse()
        
        compensation_failed = False
        
        for step in executed_steps:
            if step.compensation is None:
                logger.warning(
                    f"Saga '{self.saga_id}' - Step '{step.name}' has no compensation function"
                )
                continue
            
            try:
                logger.debug(f"Saga '{self.saga_id}' - Compensating step '{step.name}'")
                step.compensation(state)
                step.compensated = True
                logger.debug(f"Saga '{self.saga_id}' - Step '{step.name}' compensated")
            except Exception as e:
                logger.error(
                    f"Saga '{self.saga_id}' - Compensation for step '{step.name}' failed: {e}",
                    exc_info=True
                )
                compensation_failed = True
        
        if compensation_failed:
            logger.error(f"Saga '{self.saga_id}' - Compensation FAILED")
            return False
        else:
            logger.info(f"Saga '{self.saga_id}' - Compensation completed")
            return True
    
    def get_status(self) -> SagaStatus:
        """Get current saga status.
        
        Returns:
            Current status
        """
        return self.context.status
    
    def get_results(self) -> Dict[str, Any]:
        """Get results from all completed steps.
        
        Returns:
            Dictionary mapping step name to result
        """
        return self.context.results.copy()


class SagaBuilder:
    """Builder for constructing sagas fluently.
    
    Example:
        >>> saga = (SagaBuilder("trade")
        ...     .add_step("lock_items", lock_fn, unlock_fn)
        ...     .add_step("transfer", transfer_fn, reverse_transfer_fn)
        ...     .build())
    """
    
    def __init__(self, saga_id: str):
        """Initialize builder.
        
        Args:
            saga_id: Saga identifier
        """
        self._saga = Saga(saga_id)
    
    def add_step(
        self,
        name: str,
        action: Callable[[GameState], Any],
        compensation: Optional[Callable[[GameState], None]] = None
    ) -> "SagaBuilder":
        """Add a step (fluent interface).
        
        Args:
            name: Step name
            action: Action function
            compensation: Compensation function
            
        Returns:
            Self for chaining
        """
        self._saga.add_step(name, action, compensation)
        return self
    
    def build(self) -> Saga:
        """Build the saga.
        
        Returns:
            Configured saga
        """
        return self._saga

