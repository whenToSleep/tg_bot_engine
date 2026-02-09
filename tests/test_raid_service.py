"""Comprehensive tests for RaidService (World Bosses).

Tests cover:
- Positive: raid creation, attacks, completion, rewards
- Negative: invalid raids, concurrent attacks, edge cases
- Performance: stress tests with concurrent attacks
- Integration: leaderboards, contribution tracking
"""

import pytest
import asyncio
from engine.services.raid_service import (
    RaidService,
    RaidStatus,
    get_raid_service,
    reset_raid_service
)
from engine.core.state import GameState


class TestRaidServiceBasic:
    """Basic positive tests for RaidService."""
    
    def setup_method(self):
        """Setup fresh state and raid service."""
        reset_raid_service()
        self.state = GameState()
        self.service = RaidService(self.state)
    
    def test_create_raid(self):
        """Test creating a world raid."""
        raid_id = self.service.create_raid(
            raid_id="dragon_001",
            name="Ancient Dragon",
            description="A legendary dragon!",
            max_hp=1_000_000,
            duration_hours=48,
            reward_pool={"gems": 10000, "gold": 100000}
        )
        
        assert raid_id == "dragon_001"
        
        raid = self.service.get_raid_info("dragon_001")
        assert raid is not None
        assert raid["name"] == "Ancient Dragon"
        assert raid["max_hp"] == 1_000_000
        assert raid["current_hp"] == 1_000_000
        assert raid["status"] == RaidStatus.SCHEDULED.value
    
    def test_activate_raid(self):
        """Test activating a raid."""
        self.service.create_raid(
            raid_id="test_raid",
            name="Test",
            description="Test",
            max_hp=1000,
            duration_hours=1
        )
        
        self.service.activate_raid("test_raid")
        
        raid = self.service.get_raid_info("test_raid")
        assert raid["status"] == RaidStatus.ACTIVE.value
    
    @pytest.mark.asyncio
    async def test_attack_raid(self):
        """Test attacking a raid boss."""
        self.service.create_raid("boss", "Boss", "Test", max_hp=10000, duration_hours=1)
        self.service.activate_raid("boss")
        
        result = await self.service.attack_raid(
            raid_id="boss",
            player_id="player_1",
            damage=500
        )
        
        assert result.success is True
        assert result.damage_dealt == 500
        assert result.current_hp == 9500
        assert result.contribution_percent > 0
        assert result.is_defeated is False
    
    @pytest.mark.asyncio
    async def test_raid_defeat(self):
        """Test defeating a raid boss."""
        self.service.create_raid("weak_boss", "Weak", "Test", max_hp=100, duration_hours=1)
        self.service.activate_raid("weak_boss")
        
        # Attack for full HP
        result = await self.service.attack_raid("weak_boss", "player_1", damage=100)
        
        assert result.success is True
        assert result.is_defeated is True
        assert result.current_hp == 0
        
        raid = self.service.get_raid_info("weak_boss")
        assert raid["status"] == RaidStatus.COMPLETED.value
    
    @pytest.mark.asyncio
    async def test_get_leaderboard(self):
        """Test raid contribution leaderboard."""
        self.service.create_raid("leaderboard_raid", "Test", "Test", max_hp=10000, duration_hours=1)
        self.service.activate_raid("leaderboard_raid")
        
        # Multiple players attack
        await self.service.attack_raid("leaderboard_raid", "player_1", damage=500)
        await self.service.attack_raid("leaderboard_raid", "player_2", damage=300)
        await self.service.attack_raid("leaderboard_raid", "player_1", damage=200)  # player_1 again
        
        leaderboard = self.service.get_leaderboard("leaderboard_raid", top_n=10)
        
        assert len(leaderboard) == 2
        # player_1 should be first (700 total damage)
        assert leaderboard[0]["player_id"] == "player_1"
        assert leaderboard[0]["total_damage"] == 700
        assert leaderboard[1]["player_id"] == "player_2"
        assert leaderboard[1]["total_damage"] == 300


class TestRaidServiceNegative:
    """Negative tests for error handling."""
    
    def setup_method(self):
        """Setup fresh state and raid service."""
        reset_raid_service()
        self.state = GameState()
        self.service = RaidService(self.state)
    
    def test_create_duplicate_raid(self):
        """Test creating raid with duplicate ID."""
        self.service.create_raid("raid_1", "Raid", "Test", max_hp=1000, duration_hours=1)
        
        with pytest.raises(ValueError, match="already exists"):
            self.service.create_raid("raid_1", "Raid2", "Test", max_hp=2000, duration_hours=1)
    
    def test_activate_nonexistent_raid(self):
        """Test activating non-existent raid."""
        with pytest.raises(ValueError, match="not found"):
            self.service.activate_raid("nonexistent")
    
    @pytest.mark.asyncio
    async def test_attack_inactive_raid(self):
        """Test attacking inactive raid."""
        self.service.create_raid("inactive", "Test", "Test", max_hp=1000, duration_hours=1)
        # Don't activate it
        
        result = await self.service.attack_raid("inactive", "player_1", damage=100)
        
        assert result.success is False
        assert "not active" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_attack_completed_raid(self):
        """Test attacking already defeated raid."""
        self.service.create_raid("completed", "Test", "Test", max_hp=100, duration_hours=1)
        self.service.activate_raid("completed")
        
        # Defeat the boss
        await self.service.attack_raid("completed", "player_1", damage=100)
        
        # Try to attack again
        result = await self.service.attack_raid("completed", "player_2", damage=50)
        
        assert result.success is False
        assert "already" in result.message.lower() or "completed" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_attack_zero_damage(self):
        """Test attack with zero or negative damage."""
        self.service.create_raid("boss", "Test", "Test", max_hp=1000, duration_hours=1)
        self.service.activate_raid("boss")
        
        result = await self.service.attack_raid("boss", "player_1", damage=0)
        assert result.success is False
        
        result = await self.service.attack_raid("boss", "player_1", damage=-100)
        assert result.success is False
    
    @pytest.mark.asyncio
    async def test_overkill_damage(self):
        """Test attack that exceeds remaining HP."""
        self.service.create_raid("overkill", "Test", "Test", max_hp=100, duration_hours=1)
        self.service.activate_raid("overkill")
        
        # Attack with more damage than HP
        result = await self.service.attack_raid("overkill", "player_1", damage=500)
        
        assert result.success is True
        assert result.damage_dealt == 100  # Should cap at remaining HP
        assert result.current_hp == 0
        assert result.is_defeated is True


class TestRaidServiceConcurrency:
    """Concurrency and race condition tests."""
    
    def setup_method(self):
        """Setup fresh state and raid service."""
        reset_raid_service()
        self.state = GameState()
        self.service = RaidService(self.state)
    
    @pytest.mark.asyncio
    async def test_concurrent_attacks_same_player(self):
        """Test concurrent attacks from same player."""
        self.service.create_raid("concurrent", "Test", "Test", max_hp=10000, duration_hours=1)
        self.service.activate_raid("concurrent")
        
        # Launch 5 concurrent attacks from same player
        tasks = [
            self.service.attack_raid("concurrent", "player_1", damage=100)
            for _ in range(5)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert all(r.success for r in results)
        
        # Total damage should be 500
        raid = self.service.get_raid_info("concurrent")
        assert raid["current_hp"] == 9500
        
        # Leaderboard should show 500 total
        leaderboard = self.service.get_leaderboard("concurrent")
        assert leaderboard[0]["total_damage"] == 500
    
    @pytest.mark.asyncio
    async def test_concurrent_attacks_different_players(self):
        """Test concurrent attacks from different players."""
        self.service.create_raid("multiплayer", "Test", "Test", max_hp=10000, duration_hours=1)
        self.service.activate_raid("multiплayer")
        
        # 10 players attack simultaneously
        tasks = [
            self.service.attack_raid("multiплayer", f"player_{i}", damage=100)
            for i in range(10)
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert all(r.success for r in results)
        
        # Boss should have 9000 HP remaining
        raid = self.service.get_raid_info("multiплayer")
        assert raid["current_hp"] == 9000
        
        # Leaderboard should have 10 entries
        leaderboard = self.service.get_leaderboard("multiплayer")
        assert len(leaderboard) == 10
    
    @pytest.mark.asyncio
    async def test_race_condition_defeat(self):
        """Test race condition when multiple attacks would defeat boss."""
        self.service.create_raid("race_defeat", "Test", "Test", max_hp=150, duration_hours=1)
        self.service.activate_raid("race_defeat")
        
        # Launch 3 attacks of 100 damage each (total 300, but boss only has 150 HP)
        tasks = [
            self.service.attack_raid("race_defeat", f"player_{i}", damage=100)
            for i in range(3)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # At least one should succeed, and boss should be dead
        successful_attacks = [r for r in results if r.success]
        assert len(successful_attacks) >= 1
        
        raid = self.service.get_raid_info("race_defeat")
        assert raid["current_hp"] == 0
        assert raid["status"] == RaidStatus.COMPLETED.value
        
        # Total damage dealt should not exceed max HP
        total_damage = sum(r.damage_dealt for r in results if r.success)
        assert total_damage == 150


class TestRaidServicePerformance:
    """Performance and stress tests."""
    
    def setup_method(self):
        """Setup fresh state and raid service."""
        reset_raid_service()
        self.state = GameState()
        self.service = RaidService(self.state)
    
    @pytest.mark.asyncio
    async def test_massive_concurrent_attacks(self):
        """Stress test: 100 concurrent attacks."""
        self.service.create_raid(
            "stress_test",
            "Stress Boss",
            "Test",
            max_hp=10_000_000,
            duration_hours=1
        )
        self.service.activate_raid("stress_test")
        
        # 100 concurrent attacks
        tasks = [
            self.service.attack_raid("stress_test", f"player_{i}", damage=1000)
            for i in range(100)
        ]
        
        import time
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start_time
        
        # All should complete successfully
        assert all(r.success for r in results)
        
        # Should complete in reasonable time (< 5 seconds)
        assert elapsed < 5.0, f"Took too long: {elapsed:.2f}s"
        
        # Verify integrity
        raid = self.service.get_raid_info("stress_test")
        expected_hp = 10_000_000 - (100 * 1000)
        assert raid["current_hp"] == expected_hp
    
    @pytest.mark.asyncio
    async def test_sequential_vs_concurrent_performance(self):
        """Compare sequential vs concurrent attack performance."""
        # Sequential attacks
        self.service.create_raid("sequential", "Test", "Test", max_hp=10_000_000, duration_hours=1)
        self.service.activate_raid("sequential")
        
        import time
        start_time = time.time()
        for i in range(50):
            await self.service.attack_raid("sequential", f"player_{i}", damage=1000)
        sequential_time = time.time() - start_time
        
        # Concurrent attacks
        self.service.create_raid("concurrent", "Test", "Test", max_hp=10_000_000, duration_hours=1)
        self.service.activate_raid("concurrent")
        
        start_time = time.time()
        tasks = [
            self.service.attack_raid("concurrent", f"player_{i}", damage=1000)
            for i in range(50)
        ]
        await asyncio.gather(*tasks)
        concurrent_time = time.time() - start_time
        
        # Concurrent should be significantly faster
        print(f"\nSequential: {sequential_time:.3f}s, Concurrent: {concurrent_time:.3f}s")
        # Note: This test is informative, not a hard assertion
    
    @pytest.mark.asyncio
    async def test_billion_hp_boss(self):
        """Test handling boss with billions of HP."""
        self.service.create_raid(
            "titan",
            "Ancient Titan",
            "The ultimate challenge",
            max_hp=10_000_000_000,  # 10 billion HP!
            duration_hours=168  # 1 week
        )
        self.service.activate_raid("titan")
        
        # Simulate 100 attacks
        tasks = [
            self.service.attack_raid("titan", f"player_{i}", damage=1_000_000)
            for i in range(100)
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert all(r.success for r in results)
        
        raid = self.service.get_raid_info("titan")
        expected_hp = 10_000_000_000 - (100 * 1_000_000)
        assert raid["current_hp"] == expected_hp
        
        # Contribution percentages should be very small
        assert all(r.contribution_percent < 0.01 for r in results)


class TestRaidServiceEdgeCases:
    """Edge cases and boundary tests."""
    
    def setup_method(self):
        """Setup fresh state and raid service."""
        reset_raid_service()
        self.state = GameState()
        self.service = RaidService(self.state)
    
    def test_raid_with_min_hp(self):
        """Test raid with minimum HP (1)."""
        self.service.create_raid("min_hp", "Weak", "Test", max_hp=1, duration_hours=1)
        self.service.activate_raid("min_hp")
        
        raid = self.service.get_raid_info("min_hp")
        assert raid["max_hp"] == 1
    
    def test_raid_with_no_rewards(self):
        """Test raid with empty reward pool."""
        raid_id = self.service.create_raid(
            "no_rewards",
            "No Rewards",
            "Test",
            max_hp=1000,
            duration_hours=1,
            reward_pool={}
        )
        
        raid = self.service.get_raid_info(raid_id)
        assert raid["reward_pool"] == {}
    
    @pytest.mark.asyncio
    async def test_same_player_multiple_attacks(self):
        """Test tracking multiple attacks from same player."""
        self.service.create_raid("multi_attack", "Test", "Test", max_hp=10000, duration_hours=1)
        self.service.activate_raid("multi_attack")
        
        # Player attacks 5 times with different damage
        damages = [100, 200, 300, 400, 500]
        for damage in damages:
            await self.service.attack_raid("multi_attack", "player_1", damage=damage)
        
        leaderboard = self.service.get_leaderboard("multi_attack")
        assert len(leaderboard) == 1
        assert leaderboard[0]["player_id"] == "player_1"
        assert leaderboard[0]["total_damage"] == sum(damages)
        assert leaderboard[0]["attack_count"] == 5
    
    def test_get_all_raids(self):
        """Test getting all raids."""
        self.service.create_raid("raid_1", "One", "Test", max_hp=1000, duration_hours=1)
        self.service.create_raid("raid_2", "Two", "Test", max_hp=2000, duration_hours=2)
        self.service.create_raid("raid_3", "Three", "Test", max_hp=3000, duration_hours=3)
        
        all_raids = self.service.get_all_raids()
        
        assert len(all_raids) == 3
        raid_ids = [r["raid_id"] for r in all_raids]
        assert "raid_1" in raid_ids
        assert "raid_2" in raid_ids
        assert "raid_3" in raid_ids
    
    def test_get_active_raids(self):
        """Test filtering only active raids."""
        self.service.create_raid("active_1", "A1", "Test", max_hp=1000, duration_hours=1)
        self.service.create_raid("active_2", "A2", "Test", max_hp=2000, duration_hours=2)
        self.service.create_raid("inactive", "I1", "Test", max_hp=3000, duration_hours=3)
        
        self.service.activate_raid("active_1")
        self.service.activate_raid("active_2")
        # Leave inactive as SCHEDULED
        
        active_raids = self.service.get_active_raids()
        
        assert len(active_raids) == 2
        raid_ids = [r["raid_id"] for r in active_raids]
        assert "active_1" in raid_ids
        assert "active_2" in raid_ids
        assert "inactive" not in raid_ids


class TestRaidServiceGlobalSingleton:
    """Test global singleton pattern."""
    
    def test_global_raid_service(self):
        """Test global get_raid_service()."""
        reset_raid_service()
        
        service1 = get_raid_service(GameState())
        service2 = get_raid_service(GameState())
        
        # Should return same instance
        assert service1 is service2
    
    def test_reset_raid_service(self):
        """Test reset_raid_service()."""
        state = GameState()
        service1 = get_raid_service(state)
        
        reset_raid_service()
        
        service2 = get_raid_service(state)
        
        # Should be different instance after reset
        assert service1 is not service2

