"""Pytest configuration and fixtures.

This module provides reusable test fixtures for all tests.
"""

import pytest
from engine.core.state import GameState
from engine.core.executor import CommandExecutor


@pytest.fixture
def game_state() -> GameState:
    """Create a fresh game state for testing.
    
    Returns:
        Empty GameState instance
    """
    return GameState()


@pytest.fixture
def executor() -> CommandExecutor:
    """Create a command executor for testing.
    
    Returns:
        CommandExecutor instance
    """
    return CommandExecutor()


@pytest.fixture
def sample_player(game_state: GameState) -> dict:
    """Create a sample player entity.
    
    Args:
        game_state: GameState fixture
        
    Returns:
        Dictionary with player data
    """
    player_data = {
        "gold": 100,
        "attack": 10,
        "level": 1,
    }
    game_state.set_entity("player_1", player_data)
    return player_data


@pytest.fixture
def sample_mob(game_state: GameState) -> dict:
    """Create a sample mob entity.
    
    Args:
        game_state: GameState fixture
        
    Returns:
        Dictionary with mob data
    """
    mob_data = {
        "hp": 50,
        "gold_reward": 25,
    }
    game_state.set_entity("mob_1", mob_data)
    return mob_data


@pytest.fixture
def populated_state(game_state: GameState, sample_player: dict, sample_mob: dict) -> GameState:
    """Create a game state with sample entities.
    
    Args:
        game_state: GameState fixture
        sample_player: Sample player fixture
        sample_mob: Sample mob fixture
        
    Returns:
        GameState with player_1 and mob_1 already created
    """
    return game_state

