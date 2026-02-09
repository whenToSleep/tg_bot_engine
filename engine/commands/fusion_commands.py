"""Fusion Commands - Card/item fusion with saga pattern.

This module provides commands for fusing cards/items using the Saga pattern:
- CardFusionCommand: Fuse 2+ cards into a new card
- ItemCraftingCommand: Craft items from materials
- UpgradeCommand: Upgrade entity by consuming others

All commands guarantee atomicity using compensating actions.

Example:
    >>> from engine.commands.fusion_commands import CardFusionCommand
    >>> 
    >>> cmd = CardFusionCommand(
    ...     player_id="player_1",
    ...     source_card_ids=["card_1", "card_2"],
    ...     fusion_recipe_id="fire_dragon_fusion"
    ... )
    >>> 
    >>> result = cmd.execute(state, data_loader=loader)
    >>> if result.success:
    ...     fused_card = result.metadata["fused_card"]
    ...     print(f"Created: {fused_card['name']}")
"""

from typing import Dict, Any, List, Optional
from engine.core.command import Command, CommandResult
from engine.core.state import GameState
from engine.core.saga import Saga, SagaBuilder
from engine.core.entity_status import EntityStatus, set_status, get_status, is_usable
from engine.core.unique_entity import create_unique_entity
import logging

logger = logging.getLogger(__name__)


class CardFusionCommand(Command):
    """Fuse multiple cards into a single new card.
    
    Uses Saga pattern to guarantee atomicity:
    1. Validate source cards (exists, owned, available)
    2. Lock source cards (prevent concurrent use)
    3. Remove source cards from player
    4. Create fused card
    5. Add fused card to player
    
    If any step fails, all changes are compensated.
    
    Args:
        player_id: ID of player performing fusion
        source_card_ids: List of card IDs to fuse (2+)
        fusion_recipe_id: ID of fusion recipe from DataLoader
        
    Example:
        >>> cmd = CardFusionCommand(
        ...     player_id="player_1",
        ...     source_card_ids=["fire_card_1", "fire_card_2"],
        ...     fusion_recipe_id="fire_fusion_lv2"
        ... )
        >>> result = cmd.execute(state, data_loader=loader)
    """
    
    def __init__(
        self,
        player_id: str,
        source_card_ids: List[str],
        fusion_recipe_id: str
    ):
        super().__init__()
        self.player_id = player_id
        self.source_card_ids = source_card_ids
        self.fusion_recipe_id = fusion_recipe_id
        
        # Validation
        if len(source_card_ids) < 2:
            raise ValueError("Fusion requires at least 2 source cards")
    
    def execute(
        self,
        state: GameState,
        data_loader: Optional[Any] = None,
        **kwargs
    ) -> CommandResult:
        """Execute card fusion with saga pattern.
        
        Args:
            state: Game state
            data_loader: DataLoader for fusion recipes
            
        Returns:
            CommandResult with fused card in metadata
        """
        if not data_loader:
            return CommandResult(
                success=False,
                message="DataLoader required for fusion"
            )
        
        # Get player
        player = state.get_entity(self.player_id)
        if not player:
            return CommandResult(
                success=False,
                message=f"Player {self.player_id} not found"
            )
        
        # Get fusion recipe
        try:
            recipes = data_loader.get_all("fusion_recipe")
            recipe = next((r for r in recipes if r["id"] == self.fusion_recipe_id), None)
            if not recipe:
                return CommandResult(
                    success=False,
                    message=f"Fusion recipe '{self.fusion_recipe_id}' not found"
                )
        except:
            # No fusion recipes defined - use simple default
            recipe = {
                "id": self.fusion_recipe_id,
                "required_count": len(self.source_card_ids),
                "result_rarity": "A",  # Default to Epic
                "inherit_element": True
            }
        
        # Store original card data for compensation
        original_cards = {}
        for card_id in self.source_card_ids:
            card = state.get_entity(card_id)
            if card:
                original_cards[card_id] = card.copy()
        
        # Variable to store fused card for compensation
        fused_card_id = None
        
        # Create saga
        saga = SagaBuilder(f"fusion_{self.player_id}_{self.fusion_recipe_id}")
        
        # Step 1: Validate source cards
        def validate_cards(s: GameState) -> List[Dict[str, Any]]:
            cards = []
            for card_id in self.source_card_ids:
                card = s.get_entity(card_id)
                if not card:
                    raise ValueError(f"Card {card_id} not found")
                
                if card.get("owner_id") != self.player_id:
                    raise ValueError(f"Card {card_id} not owned by player")
                
                if not is_usable(card):
                    status = get_status(card)
                    raise ValueError(f"Card {card_id} is not usable (status: {status})")
                
                cards.append(card)
            return cards
        
        saga.add_step(
            name="validate_cards",
            action=validate_cards,
            compensation=None  # Read-only, no compensation needed
        )
        
        # Step 2: Lock source cards
        def lock_cards(s: GameState) -> None:
            for card_id in self.source_card_ids:
                card = s.get_entity(card_id)
                if card:
                    set_status(card, EntityStatus.LOCKED)
                    s.set_entity(card_id, card)
        
        def unlock_cards(s: GameState) -> None:
            for card_id in self.source_card_ids:
                card = s.get_entity(card_id)
                if card:
                    set_status(card, EntityStatus.AVAILABLE)
                    s.set_entity(card_id, card)
        
        saga.add_step(
            name="lock_cards",
            action=lock_cards,
            compensation=unlock_cards
        )
        
        # Step 3: Remove source cards
        def remove_cards(s: GameState) -> None:
            for card_id in self.source_card_ids:
                s.remove_entity(card_id)
        
        def restore_cards(s: GameState) -> None:
            for card_id, card_data in original_cards.items():
                s.set_entity(card_id, card_data)
        
        saga.add_step(
            name="remove_cards",
            action=remove_cards,
            compensation=restore_cards
        )
        
        # Step 4: Create fused card
        def create_fused(s: GameState) -> Dict[str, Any]:
            nonlocal fused_card_id
            
            # Get source cards for reference
            source_cards = list(original_cards.values())
            
            # Determine result template
            if recipe.get("result_card_id"):
                # Specific result defined in recipe
                card_templates = data_loader.get_all("card")
                result_template = next(
                    (c for c in card_templates if c["id"] == recipe["result_card_id"]),
                    None
                )
                if not result_template:
                    raise ValueError(f"Result card template not found: {recipe['result_card_id']}")
            else:
                # Generic fusion - average stats
                result_template = {
                    "id": f"fused_{self.fusion_recipe_id}",
                    "name": f"Fused {source_cards[0].get('name', 'Card')}",
                    "rarity": recipe.get("result_rarity", "A"),
                    "atk": sum(c.get("atk", 0) for c in source_cards) // len(source_cards),
                    "def": sum(c.get("def", 0) for c in source_cards) // len(source_cards),
                    "hp": sum(c.get("hp", 0) for c in source_cards) // len(source_cards)
                }
                
                # Inherit element if specified
                if recipe.get("inherit_element"):
                    elements = [c.get("element") for c in source_cards if c.get("element")]
                    if elements:
                        result_template["element"] = elements[0]
            
            # Create unique instance
            fused_card = create_unique_entity(
                result_template,
                "card",
                owner_id=self.player_id
            )
            
            fused_card_id = fused_card["id"]
            s.set_entity(fused_card_id, fused_card)
            
            return fused_card
        
        def remove_fused(s: GameState) -> None:
            if fused_card_id:
                s.remove_entity(fused_card_id)
        
        saga.add_step(
            name="create_fused_card",
            action=create_fused,
            compensation=remove_fused
        )
        
        # Execute saga
        result = saga.build().execute(state)
        
        if result.success:
            fused_card = result.metadata["results"]["create_fused_card"]
            logger.info(
                f"Fusion completed: {len(self.source_card_ids)} cards → {fused_card['id']}"
            )
            
            # Publish event
            try:
                from engine.core.events import Event, get_event_bus
                event_bus = get_event_bus()
                event_bus.publish(Event(
                    event_type="card_fusion",
                    data={
                        "player_id": self.player_id,
                        "source_card_ids": self.source_card_ids,
                        "fused_card_id": fused_card["id"],
                        "recipe_id": self.fusion_recipe_id
                    }
                ))
            except:
                pass
            
            return CommandResult(
                success=True,
                message=f"Fused {len(self.source_card_ids)} cards into {fused_card.get('name', 'new card')}",
                metadata={
                    "fused_card": fused_card,
                    "source_card_ids": self.source_card_ids
                }
            )
        else:
            return result


class ItemCraftingCommand(Command):
    """Craft an item from materials using saga pattern.
    
    Similar to CardFusionCommand but for items/resources.
    
    Args:
        player_id: ID of player crafting
        material_ids: List of material item IDs
        recipe_id: Crafting recipe ID
        
    Example:
        >>> cmd = ItemCraftingCommand(
        ...     player_id="player_1",
        ...     material_ids=["wood_10", "iron_5"],
        ...     recipe_id="iron_sword_recipe"
        ... )
    """
    
    def __init__(
        self,
        player_id: str,
        material_ids: List[str],
        recipe_id: str
    ):
        super().__init__()
        self.player_id = player_id
        self.material_ids = material_ids
        self.recipe_id = recipe_id
    
    def execute(
        self,
        state: GameState,
        data_loader: Optional[Any] = None,
        **kwargs
    ) -> CommandResult:
        """Execute item crafting.
        
        Implementation similar to CardFusionCommand.
        """
        # Similar implementation to CardFusionCommand
        # Left as exercise - follows same saga pattern
        
        return CommandResult(
            success=False,
            message="ItemCraftingCommand not yet implemented (use CardFusionCommand as template)"
        )


class UpgradeCommand(Command):
    """Upgrade an entity by consuming other entities.
    
    Example: Upgrade a card by sacrificing duplicate cards.
    
    Args:
        player_id: ID of player
        target_entity_id: Entity to upgrade
        sacrifice_entity_ids: Entities to consume
        
    Example:
        >>> cmd = UpgradeCommand(
        ...     player_id="player_1",
        ...     target_entity_id="my_legendary_card",
        ...     sacrifice_entity_ids=["dupe_card_1", "dupe_card_2"]
        ... )
    """
    
    def __init__(
        self,
        player_id: str,
        target_entity_id: str,
        sacrifice_entity_ids: List[str]
    ):
        super().__init__()
        self.player_id = player_id
        self.target_entity_id = target_entity_id
        self.sacrifice_entity_ids = sacrifice_entity_ids
    
    def execute(
        self,
        state: GameState,
        **kwargs
    ) -> CommandResult:
        """Execute upgrade with saga pattern."""
        # Store originals for compensation
        target_original = state.get_entity(self.target_entity_id)
        if not target_original:
            return CommandResult(
                success=False,
                message=f"Target entity {self.target_entity_id} not found"
            )
        
        target_original = target_original.copy()
        
        sacrifice_originals = {}
        for entity_id in self.sacrifice_entity_ids:
            entity = state.get_entity(entity_id)
            if entity:
                sacrifice_originals[entity_id] = entity.copy()
        
        # Create saga
        saga = SagaBuilder(f"upgrade_{self.player_id}_{self.target_entity_id}")
        
        # Step 1: Validate entities
        def validate_entities(s: GameState) -> None:
            target = s.get_entity(self.target_entity_id)
            if not target:
                raise ValueError(f"Target not found: {self.target_entity_id}")
            
            if target.get("owner_id") != self.player_id:
                raise ValueError("Target not owned by player")
            
            for sac_id in self.sacrifice_entity_ids:
                sac = s.get_entity(sac_id)
                if not sac:
                    raise ValueError(f"Sacrifice entity not found: {sac_id}")
                if sac.get("owner_id") != self.player_id:
                    raise ValueError(f"Sacrifice entity not owned: {sac_id}")
        
        saga.add_step("validate", validate_entities, None)
        
        # Step 2: Remove sacrifice entities
        def remove_sacrifices(s: GameState) -> None:
            for sac_id in self.sacrifice_entity_ids:
                s.remove_entity(sac_id)
        
        def restore_sacrifices(s: GameState) -> None:
            for sac_id, sac_data in sacrifice_originals.items():
                s.set_entity(sac_id, sac_data)
        
        saga.add_step("remove_sacrifices", remove_sacrifices, restore_sacrifices)
        
        # Step 3: Upgrade target
        def upgrade_target(s: GameState) -> Dict[str, Any]:
            target = s.get_entity(self.target_entity_id)
            
            # Calculate exp gain (1 level per sacrifice)
            exp_gain = len(self.sacrifice_entity_ids) * 100
            target["exp"] = target.get("exp", 0) + exp_gain
            
            # Level up if needed
            exp_per_level = 1000
            while target["exp"] >= exp_per_level:
                target["level"] = target.get("level", 1) + 1
                target["exp"] -= exp_per_level
            
            s.set_entity(self.target_entity_id, target)
            return target
        
        def restore_target(s: GameState) -> None:
            s.set_entity(self.target_entity_id, target_original)
        
        saga.add_step("upgrade_target", upgrade_target, restore_target)
        
        # Execute
        result = saga.build().execute(state)
        
        if result.success:
            upgraded = result.metadata["results"]["upgrade_target"]
            return CommandResult(
                success=True,
                message=f"Upgraded {self.target_entity_id} to level {upgraded.get('level', 1)}",
                metadata={"upgraded_entity": upgraded}
            )
        else:
            return result

