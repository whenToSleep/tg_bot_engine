"""Response builder for constructing Telegram messages.

This module converts game command results into formatted Telegram
messages with text and inline keyboards.
"""

from typing import Dict, Any, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

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

