"""Tests for Scheduler Service and Banner Manager.

Tests cover:
- Scheduler basic functionality (one-time, recurring tasks)
- Task cancellation
- Banner creation and activation
- Flash banner scheduling and expiration
- Race conditions
- Event integration
"""

import pytest
import asyncio
from engine.services.scheduler import SchedulerService, get_scheduler, reset_scheduler
from engine.services.banner_manager import (
    BannerManager,
    BannerStatus,
    get_banner_manager,
    reset_banner_manager
)
from engine.services.gacha_service import GachaService, PityConfig


class TestSchedulerService:
    """Tests for SchedulerService."""
    
    def setup_method(self):
        """Reset scheduler before each test."""
        reset_scheduler()
    
    @pytest.mark.asyncio
    async def test_scheduler_start_stop(self):
        """Test scheduler startup and shutdown."""
        scheduler = SchedulerService()
        
        assert not scheduler.is_running()
        
        await scheduler.start()
        assert scheduler.is_running()
        
        await scheduler.shutdown()
        assert not scheduler.is_running()
    
    @pytest.mark.asyncio
    async def test_schedule_once(self):
        """Test one-time task scheduling."""
        scheduler = SchedulerService()
        await scheduler.start()
        
        executed = []
        
        async def task():
            executed.append(True)
        
        task_id = scheduler.schedule_once(
            callback=task,
            delay_seconds=0.1,
            task_name="test_task"
        )
        
        assert task_id is not None
        assert len(executed) == 0
        
        # Wait for task to execute
        await asyncio.sleep(0.2)
        assert len(executed) == 1
        
        await scheduler.shutdown()
    
    @pytest.mark.asyncio
    async def test_schedule_recurring(self):
        """Test recurring task scheduling."""
        scheduler = SchedulerService()
        await scheduler.start()
        
        execution_count = []
        
        async def task():
            execution_count.append(1)
        
        task_id = scheduler.schedule_recurring(
            callback=task,
            interval_seconds=0.1,
            task_name="recurring_task",
            initial_delay=0.05
        )
        
        # Wait for 2-3 executions
        await asyncio.sleep(0.35)
        
        # Should have executed at least 2 times
        assert len(execution_count) >= 2
        
        scheduler.cancel_task(task_id)
        await scheduler.shutdown()
    
    @pytest.mark.asyncio
    async def test_cancel_task(self):
        """Test task cancellation."""
        scheduler = SchedulerService()
        await scheduler.start()
        
        executed = []
        
        async def task():
            executed.append(True)
        
        task_id = scheduler.schedule_once(
            callback=task,
            delay_seconds=0.5,
            task_name="cancel_me"
        )
        
        # Cancel before execution
        result = scheduler.cancel_task(task_id)
        assert result is True
        
        # Wait past original execution time
        await asyncio.sleep(0.6)
        
        # Task should not have executed
        assert len(executed) == 0
        
        await scheduler.shutdown()
    
    @pytest.mark.asyncio
    async def test_get_active_tasks(self):
        """Test getting active task information."""
        scheduler = SchedulerService()
        await scheduler.start()
        
        async def dummy_task():
            pass
        
        task_id = scheduler.schedule_once(
            callback=dummy_task,
            delay_seconds=10.0,
            task_name="long_task"
        )
        
        tasks = scheduler.get_active_tasks()
        assert task_id in tasks
        assert tasks[task_id]["name"] == "long_task"
        assert tasks[task_id]["recurring"] is False
        
        scheduler.cancel_task(task_id)
        await scheduler.shutdown()
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test that errors in tasks don't crash scheduler."""
        scheduler = SchedulerService()
        await scheduler.start()
        
        executed_after_error = []
        
        async def error_task():
            raise ValueError("Test error")
        
        async def normal_task():
            executed_after_error.append(True)
        
        # Schedule error task
        scheduler.schedule_once(
            callback=error_task,
            delay_seconds=0.05,
            task_name="error_task"
        )
        
        # Schedule normal task after error task
        scheduler.schedule_once(
            callback=normal_task,
            delay_seconds=0.1,
            task_name="normal_task"
        )
        
        await asyncio.sleep(0.2)
        
        # Normal task should still execute despite error in previous task
        assert len(executed_after_error) == 1
        
        await scheduler.shutdown()
    
    @pytest.mark.asyncio
    async def test_global_singleton(self):
        """Test global scheduler singleton."""
        reset_scheduler()
        
        scheduler1 = get_scheduler()
        scheduler2 = get_scheduler()
        
        assert scheduler1 is scheduler2
        
        reset_scheduler()
        scheduler3 = get_scheduler()
        assert scheduler3 is not scheduler1


class TestBannerManager:
    """Tests for BannerManager."""
    
    def setup_method(self):
        """Reset banner manager and scheduler before each test."""
        reset_banner_manager()
        reset_scheduler()
    
    def test_create_banner(self):
        """Test banner creation."""
        manager = BannerManager()
        
        cards = [
            {"id": "card_1", "rarity": "C"},
            {"id": "card_2", "rarity": "S"}
        ]
        
        banner_id = manager.create_banner(
            banner_id="test_banner",
            name="Test Banner",
            description="Test",
            card_pool=cards
        )
        
        assert banner_id == "test_banner"
        
        banner_info = manager.get_banner_info("test_banner")
        assert banner_info is not None
        assert banner_info["name"] == "Test Banner"
        assert banner_info["card_pool_size"] == 2
        assert banner_info["status"] == BannerStatus.SCHEDULED.value
    
    def test_create_duplicate_banner(self):
        """Test that creating duplicate banner raises error."""
        manager = BannerManager()
        cards = [{"id": "card_1", "rarity": "C"}]
        
        manager.create_banner("test", "Test", "Test", cards)
        
        with pytest.raises(ValueError, match="already exists"):
            manager.create_banner("test", "Test2", "Test2", cards)
    
    def test_activate_banner(self):
        """Test banner activation."""
        manager = BannerManager()
        cards = [{"id": "card_1", "rarity": "C"}]
        
        manager.create_banner("test", "Test", "Test", cards)
        manager.activate_banner("test")
        
        active = manager.get_active_banner()
        assert active is not None
        assert active["banner_id"] == "test"
        assert active["status"] == BannerStatus.ACTIVE.value
    
    def test_expire_banner(self):
        """Test banner expiration."""
        manager = BannerManager()
        cards = [{"id": "card_1", "rarity": "C"}]
        
        manager.create_banner("test", "Test", "Test", cards)
        manager.activate_banner("test")
        manager.expire_banner("test")
        
        banner_info = manager.get_banner_info("test")
        assert banner_info["status"] == BannerStatus.EXPIRED.value
        
        # Active banner should be None after expiration
        active = manager.get_active_banner()
        assert active is None
    
    def test_set_default_banner(self):
        """Test default banner fallback."""
        manager = BannerManager()
        cards = [{"id": "card_1", "rarity": "C"}]
        
        manager.create_banner("default", "Default", "Default", cards)
        manager.create_banner("flash", "Flash", "Flash", cards)
        
        manager.set_default_banner("default")
        
        # Default should be active
        active = manager.get_active_banner()
        assert active["banner_id"] == "default"
        
        # Activate flash banner
        manager.activate_banner("flash")
        active = manager.get_active_banner()
        assert active["banner_id"] == "flash"
        
        # Expire flash banner - should fall back to default
        manager.expire_banner("flash")
        active = manager.get_active_banner()
        assert active["banner_id"] == "default"
    
    @pytest.mark.asyncio
    async def test_flash_banner(self):
        """Test flash banner scheduling."""
        scheduler = get_scheduler()
        await scheduler.start()
        
        manager = BannerManager()
        cards = [{"id": "card_1", "rarity": "C"}]
        
        banner_id = manager.create_flash_banner(
            banner_id="flash",
            name="Flash",
            description="Flash banner",
            card_pool=cards,
            duration_seconds=0.2,  # 200ms duration
            notify_players=False
        )
        
        # Banner should activate immediately
        await asyncio.sleep(0.05)
        active = manager.get_active_banner()
        assert active is not None
        assert active["banner_id"] == "flash"
        
        # Banner should expire after duration
        await asyncio.sleep(0.3)
        banner_info = manager.get_banner_info("flash")
        assert banner_info["status"] == BannerStatus.EXPIRED.value
        
        await scheduler.shutdown()
    
    @pytest.mark.asyncio
    async def test_flash_banner_with_delay(self):
        """Test flash banner with delayed activation."""
        scheduler = get_scheduler()
        await scheduler.start()
        
        manager = BannerManager()
        cards = [{"id": "card_1", "rarity": "C"}]
        
        manager.create_flash_banner(
            banner_id="delayed",
            name="Delayed",
            description="Delayed banner",
            card_pool=cards,
            duration_seconds=0.2,
            delay_before_start=0.15,  # 150ms delay
            notify_players=False
        )
        
        # Banner should not be active immediately
        await asyncio.sleep(0.05)
        active = manager.get_active_banner()
        assert active is None
        
        # Banner should be active after delay
        await asyncio.sleep(0.15)
        active = manager.get_active_banner()
        assert active is not None
        assert active["banner_id"] == "delayed"
        
        await scheduler.shutdown()
    
    def test_track_pull(self):
        """Test pull statistics tracking."""
        manager = BannerManager()
        cards = [{"id": "card_1", "rarity": "C"}]
        
        manager.create_banner("test", "Test", "Test", cards)
        
        manager.track_pull("test", "player_1", pull_count=1)
        manager.track_pull("test", "player_2", pull_count=10)
        manager.track_pull("test", "player_1", pull_count=1)  # Same player again
        
        banner_info = manager.get_banner_info("test")
        assert banner_info["total_pulls"] == 12
        assert banner_info["unique_pullers"] == 2
    
    def test_get_all_banners(self):
        """Test getting all banners."""
        manager = BannerManager()
        cards = [{"id": "card_1", "rarity": "C"}]
        
        manager.create_banner("banner1", "Banner 1", "Test", cards)
        manager.create_banner("banner2", "Banner 2", "Test", cards)
        
        all_banners = manager.get_all_banners()
        assert len(all_banners) == 2
        
        banner_ids = [b["banner_id"] for b in all_banners]
        assert "banner1" in banner_ids
        assert "banner2" in banner_ids


class TestGachaServiceIntegration:
    """Integration tests for GachaService with BannerManager."""
    
    def setup_method(self):
        """Reset services before each test."""
        reset_banner_manager()
        reset_scheduler()
    
    def test_gacha_pull_from_active_banner(self):
        """Test pulling from active banner."""
        manager = get_banner_manager()
        gacha = GachaService()
        gacha.set_banner_manager(manager)
        
        cards = [
            {"id": "card_1", "name": "Common Card", "rarity": "C"},
            {"id": "card_2", "name": "Rare Card", "rarity": "B"}
        ]
        
        manager.create_banner("standard", "Standard", "Default", cards)
        manager.activate_banner("standard")
        
        player = {"_id": "player_1", "pity_counter": 0}
        
        result = gacha.pull_from_active_banner(player, owner_id="player_1", multi=False)
        
        assert result is not None
        assert result.card["owner_id"] == "player_1"
        assert result.rarity in ["C", "B"]
        
        # Check statistics
        banner_info = manager.get_banner_info("standard")
        assert banner_info["total_pulls"] == 1
        assert banner_info["unique_pullers"] == 1
    
    def test_gacha_multi_pull(self):
        """Test 10-pull from active banner."""
        manager = get_banner_manager()
        gacha = GachaService()
        gacha.set_banner_manager(manager)
        
        cards = [{"id": f"card_{i}", "rarity": "C"} for i in range(20)]
        cards.append({"id": "rare_card", "rarity": "A"})
        
        manager.create_banner("standard", "Standard", "Default", cards)
        manager.activate_banner("standard")
        
        player = {"_id": "player_1", "pity_counter": 0}
        
        results = gacha.pull_from_active_banner(player, owner_id="player_1", multi=True)
        
        assert results is not None
        assert len(results) == 10
        
        # Check statistics
        banner_info = manager.get_banner_info("standard")
        assert banner_info["total_pulls"] == 10
    
    def test_gacha_custom_weights(self):
        """Test custom rarity weights in banner."""
        manager = get_banner_manager()
        gacha = GachaService()
        gacha.set_banner_manager(manager)
        
        cards = [
            {"id": "common", "rarity": "C"},
            {"id": "legendary", "rarity": "S"}
        ]
        
        # Create banner with 100% S-rank rate for testing
        manager.create_banner(
            "rigged",
            "Rigged Banner",
            "100% S-rank",
            cards,
            custom_weights={"C": 0.0, "S": 100.0}
        )
        manager.activate_banner("rigged")
        
        player = {"_id": "player_1", "pity_counter": 0}
        
        # Multiple pulls should all be S-rank
        for _ in range(5):
            result = gacha.pull_from_active_banner(player, owner_id="player_1", multi=False)
            assert result.rarity == "S"


@pytest.mark.asyncio
async def test_race_condition_banner_expiration():
    """Test race condition: multiple banners expiring simultaneously."""
    scheduler = get_scheduler()
    await scheduler.start()
    
    manager = BannerManager()
    cards = [{"id": "card_1", "rarity": "C"}]
    
    # Create multiple flash banners with same expiration time
    for i in range(5):
        manager.create_flash_banner(
            banner_id=f"banner_{i}",
            name=f"Banner {i}",
            description="Test",
            card_pool=cards,
            duration_seconds=0.1,
            notify_players=False
        )
    
    # All should activate
    await asyncio.sleep(0.05)
    
    # All should expire
    await asyncio.sleep(0.15)
    
    # Verify all expired
    for i in range(5):
        banner_info = manager.get_banner_info(f"banner_{i}")
        assert banner_info["status"] == BannerStatus.EXPIRED.value
    
    await scheduler.shutdown()


@pytest.mark.asyncio
async def test_concurrent_scheduler_tasks():
    """Test many concurrent scheduler tasks."""
    scheduler = SchedulerService()
    await scheduler.start()
    
    execution_count = {"count": 0}
    
    async def increment_task():
        execution_count["count"] += 1
    
    # Schedule 20 tasks with small delays
    task_ids = []
    for i in range(20):
        task_id = scheduler.schedule_once(
            callback=increment_task,
            delay_seconds=0.01 * i,
            task_name=f"task_{i}"
        )
        task_ids.append(task_id)
    
    # Wait for all to complete
    await asyncio.sleep(0.3)
    
    assert execution_count["count"] == 20
    
    await scheduler.shutdown()

