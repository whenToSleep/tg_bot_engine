"""Response builder for constructing Telegram messages.

This module converts game command results into formatted Telegram
messages with text and inline keyboards.
"""

from typing import Dict, Any, Optional, List
from aiogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton,
    InputMediaPhoto,
    FSInputFile
)

from engine.core import CommandResult


class ResponseBuilder:
    """Builder for constructing Telegram bot responses.
    
    Converts game command results into user-friendly messages
    with appropriate formatting and inline keyboards.
    
    Example:
        >>> builder = ResponseBuilder()
        >>> response = builder.build_combat_result(command_result, mob_id="mob_123")
        >>> await message.edit_text(**response)
    """
    
    def build_combat_result(
        self, 
        result: CommandResult, 
        mob_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build response for combat command result.
        
        Args:
            result: Command execution result
            mob_id: ID of the mob (for "attack again" button)
            
        Returns:
            Dictionary with 'text' and 'reply_markup' keys
        """
        if not result.success:
            return {
                "text": f"❌ Ошибка: {result.error}",
                "reply_markup": None
            }
        
        data = result.data
        
        # Build text message
        text = f"⚔️ Вы нанесли {data.get('damage_dealt', 0)} урона!\n"
        
        if data.get('mob_killed', False):
            # Mob was killed
            text += f"💀 Моб убит!\n"
            gold_gained = data.get('gold_gained', 0)
            exp_gained = data.get('exp_gained', 0)
            
            if gold_gained > 0:
                text += f"💰 Получено золота: {gold_gained}\n"
            if exp_gained > 0:
                text += f"⭐ Получено опыта: {exp_gained}\n"
            
            keyboard = None
        else:
            # Mob still alive
            mob_hp = data.get('mob_hp', 0)
            text += f"❤️ HP моба: {mob_hp}"
            
            # Add "attack again" button if mob_id provided
            if mob_id:
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="⚔️ Атаковать ещё",
                        callback_data=f"attack:{mob_id}"
                    )]
                ])
            else:
                keyboard = None
        
        return {
            "text": text,
            "reply_markup": keyboard
        }
    
    def build_player_stats(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build player statistics message.
        
        Args:
            player_data: Player entity data
            
        Returns:
            Dictionary with 'text' and 'reply_markup' keys
        """
        gold = player_data.get('gold', 0)
        level = player_data.get('level', 1)
        exp = player_data.get('exp', 0)
        attack = player_data.get('attack', 10)
        
        text = (
            f"👤 Профиль игрока\n\n"
            f"💰 Золото: {gold}\n"
            f"⭐ Уровень: {level}\n"
            f"🎯 Опыт: {exp}\n"
            f"⚔️ Атака: {attack}\n"
        )
        
        return {"text": text, "reply_markup": None}
    
    def build_gold_result(self, result: CommandResult) -> Dict[str, Any]:
        """Build response for gold-related commands.
        
        Args:
            result: Command execution result
            
        Returns:
            Dictionary with 'text' and 'reply_markup' keys
        """
        if not result.success:
            return {
                "text": f"❌ Ошибка: {result.error}",
                "reply_markup": None
            }
        
        data = result.data
        
        if 'amount' in data:
            amount = data['amount']
            new_gold = data.get('new_gold', 0)
            
            if amount > 0:
                text = f"💰 Вы получили {amount} золота!\n\n📊 Всего золота: {new_gold}"
            else:
                text = f"💸 Вы потратили {abs(amount)} золота!\n\n📊 Осталось золота: {new_gold}"
        else:
            text = "✅ Операция выполнена успешно"
        
        return {
            "text": text,
            "reply_markup": None
        }
    
    def build_mob_spawn_result(
        self, 
        result: CommandResult, 
        mob_template_id: str
    ) -> Dict[str, Any]:
        """Build response for mob spawn command.
        
        Args:
            result: Command execution result
            mob_template_id: Template ID of spawned mob
            
        Returns:
            Dictionary with 'text' and 'reply_markup' keys
        """
        if not result.success:
            return {
                "text": f"❌ Ошибка: {result.error}",
                "reply_markup": None
            }
        
        data = result.data
        mob_id = data.get('spawned_id', '')
        hp = data.get('hp', 0)
        
        # Get mob display name from template
        mob_names = {
            'goblin_warrior': 'Гоблин-воин',
            'orc_chieftain': 'Вождь орков',
            'dragon_ancient': 'Древний дракон'
        }
        mob_name = mob_names.get(mob_template_id, mob_template_id)
        
        text = f"👹 Перед вами {mob_name}!\n❤️ HP: {hp}"
        
        # Add attack button
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="⚔️ Атаковать",
                callback_data=f"attack:{mob_id}"
            )]
        ])
        
        return {
            "text": text,
            "reply_markup": keyboard
        }
    
    def build_error(self, error_message: str) -> Dict[str, Any]:
        """Build generic error message.
        
        Args:
            error_message: Error description
            
        Returns:
            Dictionary with 'text' and 'reply_markup' keys
        """
        return {
            "text": f"❌ Ошибка: {error_message}",
            "reply_markup": None
        }
    
    def build_welcome(self) -> Dict[str, Any]:
        """Build welcome message for /start command.
        
        Returns:
            Dictionary with 'text' and 'reply_markup' keys
        """
        text = (
            "🎮 Добро пожаловать в игру!\n\n"
            "Доступные команды:\n"
            "• /fight - Сразиться с мобом\n"
            "• /profile - Ваш профиль\n"
            "• /claim_daily - Получить ежедневную награду\n"
        )
        
        return {"text": text, "reply_markup": None}
    
    def build_media_album(
        self,
        items: List[Dict[str, Any]],
        media_library: Optional[Any] = None,
        caption_formatter: Optional[callable] = None
    ) -> List[InputMediaPhoto]:
        """Build InputMediaPhoto album for batch sending (e.g., gacha x10).
        
        Creates a list of InputMediaPhoto objects that can be sent as an album
        in Telegram (instead of 10 separate messages).
        
        Args:
            items: List of items (cards, rewards, etc.) to display
            media_library: Optional MediaLibrary for file_id caching
            caption_formatter: Optional function to format caption for each item
                              Signature: (item: dict, index: int) -> str
                              
        Returns:
            List of InputMediaPhoto objects ready to send via bot.send_media_group()
            
        Example:
            >>> # Gacha 10-pull result
            >>> cards = [result.card for result in gacha_results]
            >>> album = builder.build_media_album(
            ...     cards,
            ...     media_library=get_media_library(),
            ...     caption_formatter=lambda c, i: f"{c['rarity']} - {c['name']}"
            ... )
            >>> await message.answer_media_group(album)
            
        Note:
            - Uses MediaLibrary for file_id caching if provided
            - Falls back to FSInputFile for uncached images
            - Maximum 10 items per album (Telegram limit)
        """
        media_group = []
        
        # Limit to 10 items (Telegram album limit)
        items = items[:10]
        
        for idx, item in enumerate(items):
            # Get image path
            image_path = item.get("image", f"images/{item.get('proto_id', 'unknown')}.png")
            
            # Try to get cached file_id
            file_id = None
            if media_library:
                file_id = media_library.get_file_id(image_path)
            
            # Build caption
            if caption_formatter:
                caption = caption_formatter(item, idx)
            else:
                # Default caption format
                rarity = item.get("rarity", "?")
                name = item.get("name", "Unknown")
                caption = f"{rarity} - {name}"
            
            # Create InputMediaPhoto
            if file_id:
                # Use cached file_id
                media = InputMediaPhoto(
                    media=file_id,
                    caption=caption if idx == 0 else None  # Only first has caption
                )
            else:
                # Use local file
                media = InputMediaPhoto(
                    media=FSInputFile(image_path),
                    caption=caption if idx == 0 else None
                )
            
            media_group.append(media)
        
        return media_group
    
    def build_gacha_result_text(
        self, 
        results: List[Dict[str, Any]],
        rarity_counts: Optional[Dict[str, int]] = None
    ) -> str:
        """Build text summary for gacha pull results.
        
        Args:
            results: List of gacha results (cards)
            rarity_counts: Optional pre-calculated rarity counts
            
        Returns:
            Formatted text summary
            
        Example:
            >>> text = builder.build_gacha_result_text(cards)
            >>> # Output:
            >>> # 🎰 Результаты гачи (10 круток)
            >>> # 
            >>> # C: 7 шт.
            >>> # B: 2 шт.
            >>> # A: 1 шт.
        """
        if not rarity_counts:
            # Calculate rarity counts
            rarity_counts = {}
            for result in results:
                rarity = result.get("rarity", "C")
                rarity_counts[rarity] = rarity_counts.get(rarity, 0) + 1
        
        # Rarity emojis
        rarity_emojis = {
            "C": "⚪",
            "B": "🔵",
            "A": "🟣",
            "S": "🟡",
            "SS": "🔴"
        }
        
        text = f"🎰 Результаты гачи ({len(results)} круток)\n\n"
        
        # Sort by rarity (SS > S > A > B > C)
        rarity_order = ["SS", "S", "A", "B", "C"]
        for rarity in rarity_order:
            if rarity in rarity_counts:
                emoji = rarity_emojis.get(rarity, "⬜")
                count = rarity_counts[rarity]
                text += f"{emoji} {rarity}: {count} шт.\n"
        
        return text

