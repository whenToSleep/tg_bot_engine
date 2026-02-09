"""Tests for Telegram adapter components.

Tests cover:
- Command adapter functionality
- Response builder output
- Mock-based bot interaction testing
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from aiogram import types

from engine.core import GameState, AsyncCommandExecutor, CommandResult
from engine.adapters.telegram import TelegramCommandAdapter, ResponseBuilder


class TestTelegramCommandAdapter:
    """Tests for TelegramCommandAdapter."""
    
    @pytest.fixture
    def setup(self):
        """Create adapter with mocked executor."""
        state = GameState()
        executor = AsyncCommandExecutor(state)
        adapter = TelegramCommandAdapter(executor)
        return adapter, state
    
    @pytest.mark.asyncio
    async def test_handle_attack_callback(self, setup):
        """Test handling attack callback."""
        adapter, state = setup
        
        # Setup state
        state.set_entity("123", {"_type": "player", "gold": 100, "attack": 10})
        state.set_entity("mob_1", {"_type": "mob", "template_id": "goblin_warrior", "hp": 50})
        
        # Mock callback
        callback = Mock(spec=types.CallbackQuery)
        callback.from_user = Mock(id=123)
        callback.data = "attack:mob_1"
        
        # Execute
        result = await adapter.handle_callback(callback)
        
        # Verify
        assert result.success
        assert 'damage_dealt' in result.data
        assert 'mob_hp' in result.data
    
    @pytest.mark.asyncio
    async def test_handle_buy_callback(self, setup):
        """Test handling buy callback."""
        adapter, state = setup
        
        # Setup state
        state.set_entity("123", {"_type": "player", "gold": 100})
        
        # Mock callback
        callback = Mock(spec=types.CallbackQuery)
        callback.from_user = Mock(id=123)
        callback.data = "buy:sword:50"
        
        # Execute
        result = await adapter.handle_callback(callback)
        
        # Verify
        assert result.success
        assert state.get_entity("123")["gold"] == 50
        assert 'item_id' in result.data
        assert result.data['item_id'] == 'sword'
    
    @pytest.mark.asyncio
    async def test_handle_buy_callback_insufficient_gold(self, setup):
        """Test buy callback fails with insufficient gold."""
        adapter, state = setup
        
        # Setup state
        state.set_entity("123", {"_type": "player", "gold": 10})
        
        # Mock callback
        callback = Mock(spec=types.CallbackQuery)
        callback.from_user = Mock(id=123)
        callback.data = "buy:sword:50"
        
        # Execute
        result = await adapter.handle_callback(callback)
        
        # Verify
        assert not result.success
        assert state.get_entity("123")["gold"] == 10  # Unchanged
    
    @pytest.mark.asyncio
    async def test_handle_unknown_callback(self, setup):
        """Test unknown callback returns error."""
        adapter, state = setup
        
        # Mock callback
        callback = Mock(spec=types.CallbackQuery)
        callback.from_user = Mock(id=123)
        callback.data = "unknown:action"
        
        # Execute
        result = await adapter.handle_callback(callback)
        
        # Verify
        assert not result.success
        assert "Unknown callback action" in result.error
    
    @pytest.mark.asyncio
    async def test_handle_empty_callback(self, setup):
        """Test empty callback returns error."""
        adapter, state = setup
        
        # Mock callback
        callback = Mock(spec=types.CallbackQuery)
        callback.from_user = Mock(id=123)
        callback.data = None
        
        # Execute
        result = await adapter.handle_callback(callback)
        
        # Verify
        assert not result.success
        assert "Empty callback data" in result.error
    
    @pytest.mark.asyncio
    async def test_handle_claim_daily_command(self, setup):
        """Test /claim_daily command."""
        adapter, state = setup
        
        # Setup state
        state.set_entity("123", {"_type": "player", "gold": 0})
        
        # Mock message
        message = Mock(spec=types.Message)
        message.from_user = Mock(id=123)
        message.text = "/claim_daily"
        
        # Execute
        result = await adapter.handle_command(message)
        
        # Verify
        assert result.success
        assert state.get_entity("123")["gold"] == 100
    
    @pytest.mark.asyncio
    async def test_handle_unknown_command(self, setup):
        """Test unknown command returns error."""
        adapter, state = setup
        
        # Mock message
        message = Mock(spec=types.Message)
        message.from_user = Mock(id=123)
        message.text = "/unknown"
        
        # Execute
        result = await adapter.handle_command(message)
        
        # Verify
        assert not result.success
        assert "Unknown command" in result.error
    
    def test_parse_command_args(self, setup):
        """Test command argument parsing."""
        adapter, state = setup
        
        # Test simple command
        cmd, args = adapter.parse_command_args("/buy sword 100")
        assert cmd == "/buy"
        assert args == ["sword", "100"]
        
        # Test command without args
        cmd, args = adapter.parse_command_args("/start")
        assert cmd == "/start"
        assert args == []
        
        # Test empty string
        cmd, args = adapter.parse_command_args("")
        assert cmd == ""
        assert args == []


class TestResponseBuilder:
    """Tests for ResponseBuilder."""
    
    @pytest.fixture
    def builder(self):
        """Create response builder."""
        return ResponseBuilder()
    
    def test_build_combat_result_success_mob_alive(self, builder):
        """Test building combat result when mob survives."""
        result = CommandResult.success_result({
            'damage_dealt': 10,
            'mob_hp': 40,
            'mob_killed': False
        })
        
        response = builder.build_combat_result(result, mob_id="mob_1")
        
        assert "10 урона" in response['text']
        assert "HP моба: 40" in response['text']
        assert response['reply_markup'] is not None
        assert response['reply_markup'].inline_keyboard[0][0].callback_data == "attack:mob_1"
    
    def test_build_combat_result_mob_killed(self, builder):
        """Test building combat result when mob is killed."""
        result = CommandResult.success_result({
            'damage_dealt': 50,
            'mob_hp': 0,
            'mob_killed': True,
            'gold_gained': 25,
            'exp_gained': 50
        })
        
        response = builder.build_combat_result(result)
        
        assert "50 урона" in response['text']
        assert "Моб убит" in response['text']
        assert "25" in response['text']  # gold
        assert "50" in response['text']  # exp
        assert response['reply_markup'] is None
    
    def test_build_combat_result_error(self, builder):
        """Test building combat result for error."""
        result = CommandResult.error_result("Mob not found")
        
        response = builder.build_combat_result(result)
        
        assert "❌" in response['text']
        assert "Mob not found" in response['text']
        assert response['reply_markup'] is None
    
    def test_build_player_stats(self, builder):
        """Test building player stats."""
        player_data = {
            'gold': 150,
            'level': 5,
            'exp': 250,
            'attack': 20
        }
        
        response = builder.build_player_stats(player_data)
        
        assert "Профиль" in response['text']
        assert "150" in response['text']  # gold
        assert "5" in response['text']    # level
        assert "250" in response['text']  # exp
        assert "20" in response['text']   # attack
    
    def test_build_gold_result_gain(self, builder):
        """Test building result for gaining gold."""
        result = CommandResult.success_result({
            'amount': 100,
            'new_gold': 200
        })
        
        response = builder.build_gold_result(result)
        
        assert "получили 100" in response['text']
        assert "200" in response['text']
    
    def test_build_gold_result_spend(self, builder):
        """Test building result for spending gold."""
        result = CommandResult.success_result({
            'amount': -50,
            'new_gold': 50
        })
        
        response = builder.build_gold_result(result)
        
        assert "потратили" in response['text']
        assert "50" in response['text']
    
    def test_build_mob_spawn_result(self, builder):
        """Test building mob spawn result."""
        result = CommandResult.success_result({
            'spawned_id': 'mob_123',
            'hp': 50
        })
        
        response = builder.build_mob_spawn_result(result, "goblin_warrior")
        
        assert "Гоблин-воин" in response['text']
        assert "HP: 50" in response['text']
        assert response['reply_markup'] is not None
        assert "attack:mob_123" in response['reply_markup'].inline_keyboard[0][0].callback_data
    
    def test_build_error(self, builder):
        """Test building generic error."""
        response = builder.build_error("Something went wrong")
        
        assert "❌" in response['text']
        assert "Something went wrong" in response['text']
        assert response['reply_markup'] is None
    
    def test_build_welcome(self, builder):
        """Test building welcome message."""
        response = builder.build_welcome()
        
        assert "Добро пожаловать" in response['text']
        assert "/fight" in response['text']
        assert "/profile" in response['text']
        assert "/claim_daily" in response['text']

