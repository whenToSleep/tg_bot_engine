"""Gacha Commands - Commands for gacha pulls and banner management.

This module provides commands for CCG/Gacha game mechanics:
- GachaPullCommand: Perform gacha pull from active banner
- ScheduleBannerCommand: Schedule a time-limited banner
- ExpireBannerCommand: Manually expire a banner
- CreateBannerCommand: Create a new banner

These commands integrate with BannerManager, GachaService, and Scheduler.

Example:
    >>> from engine.commands.gacha_commands import GachaPullCommand
    >>> from engine.services import get_banner_manager, GachaService
    >>> 
    >>> # Setup
    >>> manager = get_banner_manager()
    >>> gacha = GachaService()
    >>> gacha.set_banner_manager(manager)
    >>> 
    >>> # Create and activate banner
    >>> manager.create_banner("standard", "Standard", "Default", all_cards)
    >>> manager.activate_banner("standard")
    >>> 
    >>> # Perform pull
    >>> cmd = GachaPullCommand(player_id="player_123", multi=False)
    >>> result = cmd.execute(state, gacha_service=gacha)
"""

from typing import Dict, Any, List, Optional
from engine.core.command import Command, CommandResult
from engine.core.state import GameState


class GachaPullCommand(Command):
    """Perform a gacha pull from the currently active banner.
    
    Automatically deducts currency, updates pity counter, and adds card to inventory.
    
    Args:
        player_id: ID of player performing pull
        multi: If True, performs 10-pull (default: False)
        currency_type: Currency to deduct (default: "gems")
        single_cost: Cost of single pull (default: 100)
        multi_cost: Cost of 10-pull (default: 900)
        
    Example:
        >>> cmd = GachaPullCommand(player_id="player_123", multi=True)
        >>> result = cmd.execute(state, gacha_service=gacha)
        >>> if result.success:
        ...     cards = result.metadata["cards"]
        ...     print(f"Pulled {len(cards)} cards!")
    """
    
    def __init__(
        self,
        player_id: str,
        multi: bool = False,
        currency_type: str = "gems",
        single_cost: int = 100,
        multi_cost: int = 900
    ):
        super().__init__()
        self.player_id = player_id
        self.multi = multi
        self.currency_type = currency_type
        self.single_cost = single_cost
        self.multi_cost = multi_cost
    
    def execute(
        self,
        state: GameState,
        gacha_service: Optional[Any] = None,
        **kwargs
    ) -> CommandResult:
        """Execute the gacha pull.
        
        Args:
            state: Game state
            gacha_service: GachaService instance (required)
            
        Returns:
            CommandResult with pulled cards in metadata
        """
        if not gacha_service:
            return CommandResult(
                success=False,
                message="GachaService not provided"
            )
        
        # Get player
        player = state.get_entity(self.player_id)
        if not player:
            return CommandResult(
                success=False,
                message=f"Player {self.player_id} not found"
            )
        
        # Check active banner
        from engine.services.banner_manager import get_banner_manager
        banner_manager = get_banner_manager()
        active_banner = banner_manager.get_active_banner()
        
        if not active_banner:
            return CommandResult(
                success=False,
                message="No active banner available"
            )
        
        # Calculate cost
        cost = self.multi_cost if self.multi else self.single_cost
        
        # Check currency
        current_currency = player.get(self.currency_type, 0)
        if current_currency < cost:
            return CommandResult(
                success=False,
                message=f"Insufficient {self.currency_type}: need {cost}, have {current_currency}"
            )
        
        # Deduct currency
        player[self.currency_type] = current_currency - cost
        state.set_entity(self.player_id, player)
        
        # Perform pull
        try:
            result = gacha_service.pull_from_active_banner(
                player,
                owner_id=self.player_id,
                multi=self.multi
            )
            
            if not result:
                # Refund on failure
                player[self.currency_type] = current_currency
                state.set_entity(self.player_id, player)
                return CommandResult(
                    success=False,
                    message="Failed to pull from banner"
                )
            
            # Handle results
            cards = []
            if self.multi:
                # Multi-pull returns list
                for gacha_result in result:
                    card = gacha_result.card
                    state.set_entity(card["id"], card)
                    cards.append(card)
                    player["pity_counter"] = gacha_result.new_pity_counter
            else:
                # Single pull returns one result
                card = result.card
                state.set_entity(card["id"], card)
                cards.append(card)
                player["pity_counter"] = result.new_pity_counter
            
            # Update player
            state.set_entity(self.player_id, player)
            
            # Publish event to EventBus
            try:
                from engine.core.events import GachaPullEvent, get_event_bus
                event_bus = get_event_bus()
                was_pity = any(
                    (gacha_result.was_pity if self.multi else [result])[0].was_pity
                    for gacha_result in (result if self.multi else [result])
                )
                event_bus.publish(GachaPullEvent(
                    player_id=self.player_id,
                    banner_id=active_banner["banner_id"],
                    cards_pulled=[c["id"] for c in cards],
                    rarities=[c.get("rarity", "C") for c in cards],
                    was_multi=self.multi,
                    was_pity=was_pity
                ))
            except Exception as e:
                # Non-critical: event publishing failure shouldn't break pull
                pass
            
            # Build summary
            pull_type = "10-pull" if self.multi else "single pull"
            rarity_summary = {}
            for card in cards:
                rarity = card.get("rarity", "C")
                rarity_summary[rarity] = rarity_summary.get(rarity, 0) + 1
            
            summary = f"Gacha {pull_type}: " + ", ".join(
                f"{count}x {rarity}" for rarity, count in sorted(rarity_summary.items())
            )
            
            return CommandResult(
                success=True,
                message=summary,
                metadata={
                    "cards": cards,
                    "cost": cost,
                    "banner_id": active_banner["banner_id"],
                    "pity_counter": player["pity_counter"]
                }
            )
            
        except Exception as e:
            # Refund on error
            player[self.currency_type] = current_currency
            state.set_entity(self.player_id, player)
            return CommandResult(
                success=False,
                message=f"Gacha pull error: {str(e)}"
            )


class CreateBannerCommand(Command):
    """Create a new gacha banner.
    
    Args:
        banner_id: Unique banner identifier
        name: Display name
        description: Banner description
        card_pool_filter: Function to filter cards for this banner
        custom_weights: Optional custom rarity weights
        featured_cards: List of featured card IDs
        
    Example:
        >>> cmd = CreateBannerCommand(
        ...     banner_id="fire_banner",
        ...     name="Fire Rate-Up",
        ...     description="Increased fire card rates!",
        ...     card_pool_filter=lambda c: c.get("element") == "fire",
        ...     custom_weights={"S": 3.0, "SS": 1.0}
        ... )
        >>> result = cmd.execute(state, data_loader=loader)
    """
    
    def __init__(
        self,
        banner_id: str,
        name: str,
        description: str,
        card_pool_filter: Optional[callable] = None,
        custom_weights: Optional[Dict[str, float]] = None,
        featured_cards: Optional[List[str]] = None
    ):
        super().__init__()
        self.banner_id = banner_id
        self.name = name
        self.description = description
        self.card_pool_filter = card_pool_filter
        self.custom_weights = custom_weights
        self.featured_cards = featured_cards or []
    
    def execute(
        self,
        state: GameState,
        data_loader: Optional[Any] = None,
        **kwargs
    ) -> CommandResult:
        """Execute banner creation.
        
        Args:
            state: Game state
            data_loader: DataLoader instance (required if card_pool_filter is provided)
            
        Returns:
            CommandResult
        """
        from engine.services.banner_manager import get_banner_manager
        
        manager = get_banner_manager()
        
        # Build card pool
        if self.card_pool_filter and data_loader:
            all_cards = data_loader.get_all("card")
            card_pool = [c for c in all_cards if self.card_pool_filter(c)]
        else:
            card_pool = []
        
        if not card_pool:
            return CommandResult(
                success=False,
                message=f"Empty card pool for banner '{self.banner_id}'"
            )
        
        try:
            manager.create_banner(
                banner_id=self.banner_id,
                name=self.name,
                description=self.description,
                card_pool=card_pool,
                custom_weights=self.custom_weights,
                featured_cards=self.featured_cards
            )
            
            return CommandResult(
                success=True,
                message=f"Banner '{self.banner_id}' created ({len(card_pool)} cards)",
                metadata={"banner_id": self.banner_id}
            )
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Failed to create banner: {str(e)}"
            )


class ScheduleBannerCommand(Command):
    """Schedule a time-limited flash banner.
    
    Creates and automatically activates/expires a banner based on schedule.
    
    Args:
        banner_id: Unique banner identifier
        name: Display name
        description: Banner description
        card_pool_filter: Function to filter cards
        duration_seconds: How long banner stays active
        custom_weights: Optional custom rarity weights
        delay_before_start: Delay before activation (default: 0)
        notify_players: Send notifications (default: True)
        
    Example:
        >>> # Create 2-hour fire rate-up banner
        >>> cmd = ScheduleBannerCommand(
        ...     banner_id="fire_rateup",
        ...     name="Fire Festival",
        ...     description="3x S-rank rate for Fire cards!",
        ...     card_pool_filter=lambda c: c.get("element") == "fire",
        ...     duration_seconds=7200,  # 2 hours
        ...     custom_weights={"S": 4.5, "SS": 1.5}
        ... )
        >>> result = cmd.execute(state, data_loader=loader)
    """
    
    def __init__(
        self,
        banner_id: str,
        name: str,
        description: str,
        card_pool_filter: Optional[callable],
        duration_seconds: float,
        custom_weights: Optional[Dict[str, float]] = None,
        featured_cards: Optional[List[str]] = None,
        delay_before_start: float = 0,
        notify_players: bool = True
    ):
        super().__init__()
        self.banner_id = banner_id
        self.name = name
        self.description = description
        self.card_pool_filter = card_pool_filter
        self.duration_seconds = duration_seconds
        self.custom_weights = custom_weights
        self.featured_cards = featured_cards or []
        self.delay_before_start = delay_before_start
        self.notify_players = notify_players
    
    def execute(
        self,
        state: GameState,
        data_loader: Optional[Any] = None,
        **kwargs
    ) -> CommandResult:
        """Execute banner scheduling.
        
        Args:
            state: Game state
            data_loader: DataLoader instance (required)
            
        Returns:
            CommandResult
        """
        from engine.services.banner_manager import get_banner_manager
        
        manager = get_banner_manager()
        
        # Build card pool
        if not data_loader:
            return CommandResult(
                success=False,
                message="DataLoader required for ScheduleBannerCommand"
            )
        
        all_cards = data_loader.get_all("card")
        if self.card_pool_filter:
            card_pool = [c for c in all_cards if self.card_pool_filter(c)]
        else:
            card_pool = all_cards
        
        if not card_pool:
            return CommandResult(
                success=False,
                message=f"Empty card pool for banner '{self.banner_id}'"
            )
        
        try:
            manager.create_flash_banner(
                banner_id=self.banner_id,
                name=self.name,
                description=self.description,
                card_pool=card_pool,
                duration_seconds=self.duration_seconds,
                custom_weights=self.custom_weights,
                featured_cards=self.featured_cards,
                delay_before_start=self.delay_before_start,
                notify_players=self.notify_players
            )
            
            activation_time = "now" if self.delay_before_start == 0 else f"in {self.delay_before_start}s"
            
            return CommandResult(
                success=True,
                message=(
                    f"Flash banner '{self.banner_id}' scheduled "
                    f"(starts: {activation_time}, duration: {self.duration_seconds}s)"
                ),
                metadata={
                    "banner_id": self.banner_id,
                    "duration_seconds": self.duration_seconds,
                    "delay_before_start": self.delay_before_start
                }
            )
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Failed to schedule banner: {str(e)}"
            )


class ExpireBannerCommand(Command):
    """Manually expire a banner.
    
    Args:
        banner_id: ID of banner to expire
        
    Example:
        >>> cmd = ExpireBannerCommand(banner_id="fire_event")
        >>> result = cmd.execute(state)
    """
    
    def __init__(self, banner_id: str):
        super().__init__()
        self.banner_id = banner_id
    
    def execute(self, state: GameState, **kwargs) -> CommandResult:
        """Execute banner expiration.
        
        Args:
            state: Game state
            
        Returns:
            CommandResult
        """
        from engine.services.banner_manager import get_banner_manager
        
        manager = get_banner_manager()
        
        try:
            manager.expire_banner(self.banner_id)
            return CommandResult(
                success=True,
                message=f"Banner '{self.banner_id}' expired",
                metadata={"banner_id": self.banner_id}
            )
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Failed to expire banner: {str(e)}"
            )


class ActivateBannerCommand(Command):
    """Activate a banner (make it the current active banner).
    
    Args:
        banner_id: ID of banner to activate
        
    Example:
        >>> cmd = ActivateBannerCommand(banner_id="standard")
        >>> result = cmd.execute(state)
    """
    
    def __init__(self, banner_id: str):
        super().__init__()
        self.banner_id = banner_id
    
    def execute(self, state: GameState, **kwargs) -> CommandResult:
        """Execute banner activation.
        
        Args:
            state: Game state
            
        Returns:
            CommandResult
        """
        from engine.services.banner_manager import get_banner_manager
        
        manager = get_banner_manager()
        
        try:
            manager.activate_banner(self.banner_id)
            return CommandResult(
                success=True,
                message=f"Banner '{self.banner_id}' activated",
                metadata={"banner_id": self.banner_id}
            )
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Failed to activate banner: {str(e)}"
            )

