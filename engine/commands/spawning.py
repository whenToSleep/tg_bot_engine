"""Spawning commands - Commands for creating entities from templates.

Provides commands to spawn game entities (mobs, items) from JSON templates
loaded by DataLoader.
"""

from typing import List, Any, Dict
from engine.core.command import Command
from engine.core.state import GameState
from engine.core.data_loader import get_global_loader, DataLoaderError
from engine.core.events import get_event_bus, MobSpawnedEvent, ItemSpawnedEvent


class SpawnMobCommand(Command):
    """Command to spawn a mob from JSON template.
    
    Creates a mob entity from a template loaded from JSON data.
    Each spawned mob gets a unique instance ID.
    
    Example:
        >>> cmd = SpawnMobCommand("goblin_warrior", "mob_instance_1")
        >>> result = executor.execute(cmd, state)
        >>> print(result.data['spawned_id'])
        mob_instance_1
    """
    
    def __init__(self, mob_template_id: str, instance_id: str) -> None:
        """Initialize SpawnMobCommand.
        
        Args:
            mob_template_id: ID of mob template in JSON data
            instance_id: Unique ID for this mob instance
        """
        self.mob_template_id = mob_template_id
        self.instance_id = instance_id
    
    def get_entity_dependencies(self) -> List[str]:
        """Get entity dependencies."""
        return [self.instance_id]
    
    def execute(self, state: GameState) -> Dict[str, Any]:
        """Execute mob spawning.
        
        Args:
            state: Game state
            
        Returns:
            Spawn result with mob data
            
        Raises:
            ValueError: If instance_id already exists or template not found
        """
        # Check if instance already exists
        if state.exists(self.instance_id):
            raise ValueError(
                f"Entity with ID '{self.instance_id}' already exists"
            )
        
        # Get data loader
        loader = get_global_loader()
        
        # Ensure mobs are loaded
        if not loader.is_loaded("mobs"):
            try:
                loader.load_category("mobs", "mob_schema.json")
            except DataLoaderError as e:
                raise ValueError(f"Failed to load mob data: {e}")
        
        # Get mob template
        mob_template = loader.get("mobs", self.mob_template_id)
        
        if mob_template is None:
            raise ValueError(
                f"Mob template '{self.mob_template_id}' not found"
            )
        
        # Create mob instance from template
        mob_instance = {
            "_type": "mob",
            "_template_id": self.mob_template_id,
            **mob_template,  # Copy all template data
            "current_hp": mob_template["hp"],  # Track current HP separately
            "id": self.instance_id,  # Override ID with instance ID
            "abilities_cooldowns": {},  # Track ability cooldowns
        }
        
        # Set entity in state
        state.set_entity(self.instance_id, mob_instance)
        
        # Publish MobSpawnedEvent
        event_bus = get_event_bus()
        event_bus.publish(MobSpawnedEvent(
            mob_id=self.instance_id,
            template_id=self.mob_template_id
        ))
        
        return {
            "spawned_id": self.instance_id,
            "template_id": self.mob_template_id,
            "name": mob_template["name"],
            "hp": mob_template["hp"],
            "attack": mob_template["attack"],
        }


class SpawnItemCommand(Command):
    """Command to spawn an item from JSON template.
    
    Creates an item entity from a template loaded from JSON data.
    
    Example:
        >>> cmd = SpawnItemCommand("rusty_sword", "item_1", quantity=1)
        >>> result = executor.execute(cmd, state)
    """
    
    def __init__(
        self, 
        item_template_id: str, 
        instance_id: str,
        quantity: int = 1
    ) -> None:
        """Initialize SpawnItemCommand.
        
        Args:
            item_template_id: ID of item template in JSON data
            instance_id: Unique ID for this item instance
            quantity: Quantity to spawn (for stackable items)
        """
        self.item_template_id = item_template_id
        self.instance_id = instance_id
        self.quantity = quantity
        
        if quantity < 1:
            raise ValueError("Quantity must be at least 1")
    
    def get_entity_dependencies(self) -> List[str]:
        """Get entity dependencies."""
        return [self.instance_id]
    
    def execute(self, state: GameState) -> Dict[str, Any]:
        """Execute item spawning.
        
        Args:
            state: Game state
            
        Returns:
            Spawn result with item data
            
        Raises:
            ValueError: If instance_id already exists or template not found
        """
        # Check if instance already exists
        if state.exists(self.instance_id):
            raise ValueError(
                f"Entity with ID '{self.instance_id}' already exists"
            )
        
        # Get data loader
        loader = get_global_loader()
        
        # Ensure items are loaded
        if not loader.is_loaded("items"):
            try:
                loader.load_category("items", "item_schema.json")
            except DataLoaderError as e:
                raise ValueError(f"Failed to load item data: {e}")
        
        # Get item template
        item_template = loader.get("items", self.item_template_id)
        
        if item_template is None:
            raise ValueError(
                f"Item template '{self.item_template_id}' not found"
            )
        
        # Validate quantity for stackable items
        if not item_template.get("stackable", False) and self.quantity > 1:
            raise ValueError(
                f"Item '{self.item_template_id}' is not stackable"
            )
        
        max_stack = item_template.get("max_stack", 1)
        if self.quantity > max_stack:
            raise ValueError(
                f"Quantity {self.quantity} exceeds max stack {max_stack}"
            )
        
        # Create item instance from template
        item_instance = {
            "_type": "item",
            "_template_id": self.item_template_id,
            **item_template,  # Copy all template data
            "id": self.instance_id,  # Override ID with instance ID
            "quantity": self.quantity,  # Current quantity
        }
        
        # Set entity in state
        state.set_entity(self.instance_id, item_instance)
        
        # Publish ItemSpawnedEvent
        event_bus = get_event_bus()
        event_bus.publish(ItemSpawnedEvent(
            item_id=self.instance_id,
            template_id=self.item_template_id,
            quantity=self.quantity
        ))
        
        return {
            "spawned_id": self.instance_id,
            "template_id": self.item_template_id,
            "name": item_template["name"],
            "quantity": self.quantity,
            "type": item_template["type"],
            "rarity": item_template.get("rarity", "common"),
        }

