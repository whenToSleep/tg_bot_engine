"""Integration and stress tests for v0.6.0 features.

Tests cover:
- Integration: all new features working together
- Stress: high load scenarios
- Performance: benchmarks for critical paths
- End-to-end: complete game flows
"""

import pytest
import asyncio
import time
from engine.core.state import GameState
from engine.services.scheduler import get_scheduler, reset_scheduler
from engine.services.banner_manager import get_banner_manager, reset_banner_manager
from engine.services.gacha_service import GachaService, PityConfig
from engine.services.raid_service import get_raid_service, reset_raid_service
from engine.core.group_bonuses import GroupBonusCalculator, create_element_synergy_rule
from engine.commands.fusion_commands import CardFusionCommand
from engine.core.executor import CommandExecutor
import tempfile
import os


class TestV060Integration:
    """Integration tests combining multiple v0.6.0 features."""
    
    @pytest.mark.asyncio
    async def test_complete_game_flow(self):
        """Test complete game flow using all v0.6.0 features."""
        # Setup
        reset_scheduler()
        reset_banner_manager()
        reset_raid_service()
        
        state = GameState()
        scheduler = get_scheduler()
        await scheduler.start()
        
        banner_mgr = get_banner_manager(state)
        raid_service = get_raid_service(state)
        gacha = GachaService(PityConfig())
        gacha.set_banner_manager(banner_mgr)
        
        # Create player
        player = {
            "_id": "player_1",
            "_type": "player",
            "name": "Test Player",
            "gems": 10000,
            "pity_counter": 0
        }
        state.set_entity("player_1", player)
        
        # 1. Create and activate banner
        cards = [
            {"id": "fire_dragon", "name": "Fire Dragon", "rarity": "S", "element": "fire"},
            {"id": "water_spirit", "name": "Water Spirit", "rarity": "A", "element": "water"},
            {"id": "earth_golem", "name": "Earth Golem", "rarity": "B", "element": "earth"}
        ]
        
        banner_mgr.create_banner("test_banner", "Test Banner", "Test", cards)
        banner_mgr.activate_banner("test_banner")
        
        # 2. Player pulls from banner
        pulled_cards = []
        for _ in range(10):
            result = gacha.pull_from_active_banner(player, owner_id="player_1", multi=False)
            if result:
                state.set_entity(result.card["_id"], result.card)
                pulled_cards.append(result.card)
        
        assert len(pulled_cards) == 10
        
        # 3. Analyze deck synergies
        calculator = GroupBonusCalculator()
        calculator.add_rule("fire", create_element_synergy_rule("fire", 3, "attack", 25))
        
        bonuses = calculator.calculate_bonuses(pulled_cards)
        print(f"\nDeck bonuses: {bonuses}")
        
        # 4. Create world raid
        raid_id = raid_service.create_raid(
            "test_raid",
            "Test Boss",
            "Epic boss",
            max_hp=100000,
            duration_hours=1
        )
        raid_service.activate_raid(raid_id)
        
        # 5. Player attacks raid
        total_power = sum(card.get("attack", 100) for card in pulled_cards[:5])
        result = await raid_service.attack_raid(raid_id, "player_1", damage=total_power)
        
        assert result.success is True
        assert result.damage_dealt > 0
        
        # Cleanup
        await scheduler.shutdown()
    
    @pytest.mark.asyncio
    async def test_banner_rotation_with_raids(self):
        """Test automatic banner rotation during raid event."""
        reset_scheduler()
        reset_banner_manager()
        reset_raid_service()
        
        state = GameState()
        scheduler = get_scheduler()
        await scheduler.start()
        
        banner_mgr = get_banner_manager(state)
        raid_service = get_raid_service(state)
        
        cards = [{"id": f"card_{i}", "rarity": "C"} for i in range(10)]
        
        # Create raid
        raid_service.create_raid("raid_1", "Boss 1", "Test", max_hp=1000000, duration_hours=1)
        raid_service.activate_raid("raid_1")
        
        # Create flash banner
        banner_mgr.create_flash_banner(
            "flash_1",
            "Flash Banner",
            "Test",
            cards,
            duration_seconds=0.2,
            notify_players=False
        )
        
        # Wait for banner activation
        await asyncio.sleep(0.1)
        
        # Banner should be active while raid is active
        active_banner = banner_mgr.get_active_banner()
        raid_info = raid_service.get_raid_info("raid_1")
        
        assert active_banner is not None
        assert raid_info["status"] == "active"
        
        await scheduler.shutdown()
    
    @pytest.mark.asyncio
    async def test_fusion_with_raid_rewards(self):
        """Test fusing cards obtained from raid rewards."""
        state = GameState()
        
        # Create player
        state.set_entity("player_1", {"_id": "player_1", "_type": "player"})
        
        # Simulate raid reward cards
        state.set_entity("card_1", {
            "_id": "card_1",
            "_type": "card",
            "owner_id": "player_1",
            "element": "fire",
            "rarity": "B",
            "status": "AVAILABLE"
        })
        state.set_entity("card_2", {
            "_id": "card_2",
            "_type": "card",
            "owner_id": "player_1",
            "element": "fire",
            "rarity": "B",
            "status": "AVAILABLE"
        })
        
        # Mock data loader
        class MockDataLoader:
            def get_all(self, entity_type):
                if entity_type == "card":
                    return [{"id": "fire_knight", "rarity": "A", "element": "fire"}]
                return []
        
        # Fuse cards
        fusion_cmd = CardFusionCommand(
            player_id="player_1",
            source_card_ids=["card_1", "card_2"],
            fusion_recipe_id="fire_fusion"
        )
        
        result = fusion_cmd.execute(state, data_loader=MockDataLoader())
        
        assert result.success is True
        assert "fused_card" in result.metadata


class TestV060StressTests:
    """Stress tests for v0.6.0 features under load."""
    
    @pytest.mark.asyncio
    async def test_concurrent_gacha_pulls_from_banner(self):
        """Stress: 100 players pulling simultaneously from same banner."""
        reset_banner_manager()
        
        state = GameState()
        banner_mgr = get_banner_manager(state)
        gacha = GachaService()
        gacha.set_banner_manager(banner_mgr)
        
        # Create banner with many cards
        cards = [
            {"id": f"card_{i}", "name": f"Card {i}", "rarity": ["C", "B", "A", "S"][i % 4]}
            for i in range(100)
        ]
        
        banner_mgr.create_banner("stress_banner", "Stress", "Test", cards)
        banner_mgr.activate_banner("stress_banner")
        
        # 100 players pull simultaneously
        async def player_pull(player_id):
            player = {"_id": player_id, "pity_counter": 0}
            result = gacha.pull_from_active_banner(player, owner_id=player_id, multi=False)
            return result is not None
        
        tasks = [player_pull(f"player_{i}") for i in range(100)]
        
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start_time
        
        # All pulls should succeed
        assert all(results)
        
        # Should complete quickly
        assert elapsed < 2.0, f"Took too long: {elapsed:.2f}s"
        
        # Check banner stats
        banner_info = banner_mgr.get_banner_info("stress_banner")
        assert banner_info["total_pulls"] == 100
        assert banner_info["unique_pullers"] == 100
        
        print(f"\n100 concurrent pulls in {elapsed:.3f}s ({elapsed*10:.2f}ms per pull)")
    
    @pytest.mark.asyncio
    async def test_multiple_raids_concurrent_attacks(self):
        """Stress: Multiple active raids with concurrent attacks."""
        reset_raid_service()
        
        state = GameState()
        raid_service = get_raid_service(state)
        
        # Create 5 raids
        raid_ids = []
        for i in range(5):
            raid_id = raid_service.create_raid(
                f"raid_{i}",
                f"Boss {i}",
                "Test",
                max_hp=1_000_000,
                duration_hours=1
            )
            raid_service.activate_raid(raid_id)
            raid_ids.append(raid_id)
        
        # 50 players attack each raid (250 total attacks)
        async def attack_all_raids(player_id):
            results = []
            for raid_id in raid_ids:
                result = await raid_service.attack_raid(raid_id, player_id, damage=1000)
                results.append(result.success)
            return all(results)
        
        tasks = [attack_all_raids(f"player_{i}") for i in range(50)]
        
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start_time
        
        # All attacks should succeed
        assert all(results)
        
        # Verify all raids took damage
        for raid_id in raid_ids:
            raid_info = raid_service.get_raid_info(raid_id)
            expected_hp = 1_000_000 - (50 * 1000)
            assert raid_info["current_hp"] == expected_hp
        
        print(f"\n250 concurrent raid attacks in {elapsed:.3f}s")
    
    @pytest.mark.asyncio
    async def test_scheduler_overload(self):
        """Stress: Schedule 1000 tasks rapidly."""
        reset_scheduler()
        
        scheduler = get_scheduler()
        await scheduler.start()
        
        execution_count = {"count": 0}
        
        async def increment():
            execution_count["count"] += 1
        
        # Schedule 1000 tasks
        start_time = time.time()
        task_ids = []
        for i in range(1000):
            task_id = scheduler.schedule_once(
                callback=increment,
                delay_seconds=0.01 * (i % 10),  # Stagger execution
                task_name=f"task_{i}"
            )
            task_ids.append(task_id)
        
        scheduling_time = time.time() - start_time
        
        # Wait for all to complete
        await asyncio.sleep(0.2)
        
        # All should execute
        assert execution_count["count"] == 1000
        
        # Scheduling itself should be fast
        assert scheduling_time < 1.0, f"Scheduling took too long: {scheduling_time:.2f}s"
        
        print(f"\nScheduled 1000 tasks in {scheduling_time:.3f}s")
        
        await scheduler.shutdown()
    
    def test_massive_synergy_calculations(self):
        """Stress: Calculate synergies for 1000 decks."""
        calculator = GroupBonusCalculator()
        
        # Add multiple rules
        for element in ["fire", "water", "earth", "wind", "light", "dark"]:
            calculator.add_rule(
                f"{element}_synergy",
                create_element_synergy_rule(element, 3, "attack", 10)
            )
        
        # Create 1000 random decks
        import random
        decks = []
        elements = ["fire", "water", "earth", "wind", "light", "dark"]
        
        for _ in range(1000):
            deck = []
            for j in range(30):
                deck.append({
                    "element": random.choice(elements),
                    "name": f"Card{j}"
                })
            decks.append(deck)
        
        # Calculate bonuses for all decks
        start_time = time.time()
        results = []
        for deck in decks:
            bonuses = calculator.calculate_bonuses(deck)
            results.append(bonuses)
        elapsed = time.time() - start_time
        
        # Should complete reasonably fast
        assert elapsed < 5.0, f"Took too long: {elapsed:.2f}s"
        
        # All should have results
        assert len(results) == 1000
        
        print(f"\nCalculated synergies for 1000 decks in {elapsed:.3f}s ({elapsed:.3f}ms per deck)")


class TestV060Performance:
    """Performance benchmarks for v0.6.0 features."""
    
    @pytest.mark.asyncio
    async def test_raid_attack_latency(self):
        """Benchmark: Measure raid attack latency."""
        reset_raid_service()
        
        state = GameState()
        raid_service = get_raid_service(state)
        
        raid_service.create_raid("bench_raid", "Bench", "Test", max_hp=1_000_000, duration_hours=1)
        raid_service.activate_raid("bench_raid")
        
        # Measure 100 sequential attacks
        latencies = []
        for i in range(100):
            start = time.time()
            await raid_service.attack_raid("bench_raid", f"player_{i}", damage=1000)
            latency = (time.time() - start) * 1000  # ms
            latencies.append(latency)
        
        avg_latency = sum(latencies) / len(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
        p99_latency = sorted(latencies)[int(len(latencies) * 0.99)]
        
        print(f"\nRaid attack latency:")
        print(f"  Average: {avg_latency:.2f}ms")
        print(f"  P95: {p95_latency:.2f}ms")
        print(f"  P99: {p99_latency:.2f}ms")
        
        # Performance target: p99 < 50ms
        assert p99_latency < 50, f"p99 latency too high: {p99_latency:.2f}ms"
    
    def test_banner_pull_throughput(self):
        """Benchmark: Measure gacha pull throughput."""
        reset_banner_manager()
        
        state = GameState()
        banner_mgr = get_banner_manager(state)
        gacha = GachaService()
        gacha.set_banner_manager(banner_mgr)
        
        cards = [{"id": f"card_{i}", "rarity": "C"} for i in range(50)]
        banner_mgr.create_banner("bench", "Bench", "Test", cards)
        banner_mgr.activate_banner("bench")
        
        player = {"_id": "bench_player", "pity_counter": 0}
        
        # Measure throughput
        start_time = time.time()
        pulls_count = 0
        
        duration = 1.0  # 1 second
        while time.time() - start_time < duration:
            gacha.pull_from_active_banner(player, owner_id="bench_player", multi=False)
            pulls_count += 1
        
        elapsed = time.time() - start_time
        throughput = pulls_count / elapsed
        
        print(f"\nGacha pull throughput: {throughput:.0f} pulls/sec")
        
        # Performance target: > 100 pulls/sec
        assert throughput > 100, f"Throughput too low: {throughput:.0f} pulls/sec"
    
    def test_synergy_calculation_speed(self):
        """Benchmark: Synergy calculation performance."""
        calculator = GroupBonusCalculator()
        
        # Add 10 rules
        for i in range(10):
            calculator.add_rule(
                f"rule_{i}",
                create_element_synergy_rule("fire", 3, f"stat_{i}", 10)
            )
        
        # Large deck
        deck = [{"element": "fire", "name": f"Card{i}"} for i in range(50)]
        
        # Measure speed
        start_time = time.time()
        iterations = 10000
        
        for _ in range(iterations):
            calculator.calculate_bonuses(deck)
        
        elapsed = time.time() - start_time
        rate = iterations / elapsed
        
        print(f"\nSynergy calculation rate: {rate:.0f} calcs/sec")
        
        # Performance target: > 1000 calcs/sec
        assert rate > 1000, f"Rate too low: {rate:.0f} calcs/sec"


class TestV060EndToEnd:
    """End-to-end scenario tests."""
    
    @pytest.mark.asyncio
    async def test_weekly_raid_event_scenario(self):
        """E2E: Simulate weekly raid event with banners."""
        reset_scheduler()
        reset_banner_manager()
        reset_raid_service()
        
        state = GameState()
        scheduler = get_scheduler()
        await scheduler.start()
        
        banner_mgr = get_banner_manager(state)
        raid_service = get_raid_service(state)
        gacha = GachaService()
        gacha.set_banner_manager(banner_mgr)
        
        # Week-long raid event
        raid_service.create_raid(
            "weekly_titan",
            "Ancient Titan",
            "Weekly challenge",
            max_hp=10_000_000,
            duration_hours=168,  # 1 week
            reward_pool={"gems": 100000, "gold": 1000000}
        )
        raid_service.activate_raid("weekly_titan")
        
        # Special banner for the event
        event_cards = [
            {"id": "titan_slayer", "rarity": "S", "element": "fire", "attack": 500},
            {"id": "dragon_knight", "rarity": "A", "element": "water", "attack": 300}
        ]
        
        banner_mgr.create_banner("event_banner", "Titan Slayer Banner", "Event", event_cards)
        banner_mgr.activate_banner("event_banner")
        
        # Simulate 10 players participating
        for player_id in range(10):
            # Create player
            player = {
                "_id": f"player_{player_id}",
                "pity_counter": 0
            }
            state.set_entity(f"player_{player_id}", player)
            
            # Player pulls from banner
            result = gacha.pull_from_active_banner(player, owner_id=f"player_{player_id}", multi=False)
            if result:
                # Player attacks raid with pulled card
                damage = result.card.get("attack", 200)
                await raid_service.attack_raid("weekly_titan", f"player_{player_id}", damage=damage)
        
        # Check raid progress
        raid_info = raid_service.get_raid_info("weekly_titan")
        assert raid_info["current_hp"] < 10_000_000  # Some damage dealt
        
        # Check leaderboard
        leaderboard = raid_service.get_leaderboard("weekly_titan")
        assert len(leaderboard) == 10
        
        await scheduler.shutdown()


@pytest.mark.asyncio
async def test_full_system_integration():
    """Test all v0.6.0 features working together in complex scenario."""
    # Reset all services
    reset_scheduler()
    reset_banner_manager()
    reset_raid_service()
    
    state = GameState()
    scheduler = get_scheduler()
    await scheduler.start()
    
    banner_mgr = get_banner_manager(state)
    raid_service = get_raid_service(state)
    gacha = GachaService()
    gacha.set_banner_manager(banner_mgr)
    calculator = GroupBonusCalculator()
    
    # Add synergy rules
    calculator.add_rule("fire", create_element_synergy_rule("fire", 3, "attack", 50))
    calculator.add_rule("water", create_element_synergy_rule("water", 3, "defense", 30))
    
    # Create card pool
    all_cards = []
    for i in range(20):
        all_cards.append({
            "id": f"card_{i}",
            "name": f"Card {i}",
            "element": ["fire", "water", "earth"][i % 3],
            "rarity": ["C", "B", "A", "S"][i % 4],
            "attack": 100 + (i * 10)
        })
    
    # Create multiple banners
    banner_mgr.create_banner("standard", "Standard", "Always available", all_cards[:10])
    banner_mgr.set_default_banner("standard")
    
    # Create flash event banner
    banner_mgr.create_flash_banner(
        "flash_event",
        "Flash Event",
        "Limited time!",
        all_cards[10:20],
        duration_seconds=0.3,
        notify_players=False
    )
    
    # Create world raid
    raid_service.create_raid(
        "world_boss",
        "World Boss",
        "Epic challenge",
        max_hp=1_000_000,
        duration_hours=24
    )
    raid_service.activate_raid("world_boss")
    
    # Simulate player activity
    await asyncio.sleep(0.15)  # Let flash banner activate
    
    # Player pulls from active banner
    player = {"_id": "test_player", "pity_counter": 0}
    state.set_entity("test_player", player)
    
    player_cards = []
    for _ in range(10):
        result = gacha.pull_from_active_banner(player, owner_id="test_player", multi=False)
        if result:
            state.set_entity(result.card["_id"], result.card)
            player_cards.append(result.card)
    
    # Analyze deck
    bonuses = calculator.calculate_bonuses(player_cards)
    print(f"\nPlayer deck bonuses: {bonuses}")
    
    # Attack raid with powered-up deck
    total_power = sum(card.get("attack", 100) for card in player_cards)
    attack_bonus = bonuses.get("attack", 0)
    final_damage = int(total_power * (1 + attack_bonus / 100))
    
    result = await raid_service.attack_raid("world_boss", "test_player", damage=final_damage)
    assert result.success is True
    
    print(f"Total power: {total_power}, Bonus: {attack_bonus}%, Final damage: {final_damage}")
    
    # Check system state
    assert banner_mgr.get_active_banner() is not None
    assert raid_service.get_raid_info("world_boss")["status"] == "active"
    
    await scheduler.shutdown()

