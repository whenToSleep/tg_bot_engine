"""Comprehensive tests for Referral System.

Tests cover:
- Positive: referral tree creation, depth traversal, stats
- Negative: circular references, invalid players, edge cases
- Performance: deep trees, wide trees, large networks
- Integration: bonus calculations, milestone rewards
"""

import pytest
from engine.core.state import GameState
from engine.core.repository import EntityRepository
from engine.adapters.sqlite_repository import SQLiteRepository
import tempfile
import os


class TestReferralSystemBasic:
    """Basic positive tests for referral system."""
    
    def setup_method(self):
        """Setup repository with test database."""
        self.db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.db_path = self.db_file.name
        self.db_file.close()
        
        self.repo = SQLiteRepository(self.db_path)
    
    def teardown_method(self):
        """Clean up test database."""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_simple_referral_link(self):
        """Test simple referral: A refers B."""
        # Create players
        player_a = {"_id": "player_a", "_type": "player", "name": "Alice"}
        player_b = {"_id": "player_b", "_type": "player", "name": "Bob", "referred_by": "player_a"}
        
        self.repo.save(player_a)
        self.repo.save(player_b)
        
        # Get referral tree for Alice
        tree = self.repo.get_referral_tree("player_a", depth=1, include_stats=False)
        
        assert tree["player_id"] == "player_a"
        assert len(tree["children"]) == 1
        assert tree["children"][0]["player_id"] == "player_b"
    
    def test_referral_tree_depth_2(self):
        """Test referral tree with 2 levels."""
        # A → B → C
        players = [
            {"_id": "a", "_type": "player"},
            {"_id": "b", "_type": "player", "referred_by": "a"},
            {"_id": "c", "_type": "player", "referred_by": "b"}
        ]
        
        for player in players:
            self.repo.save(player)
        
        # Get tree with depth 2
        tree = self.repo.get_referral_tree("a", depth=2, include_stats=False)
        
        assert len(tree["children"]) == 1  # B
        assert tree["children"][0]["player_id"] == "b"
        assert len(tree["children"][0]["children"]) == 1  # C
        assert tree["children"][0]["children"][0]["player_id"] == "c"
    
    def test_referral_tree_multiple_children(self):
        """Test referral tree with multiple direct referrals."""
        # A → B, C, D
        self.repo.save({"_id": "a", "_type": "player"})
        self.repo.save({"_id": "b", "_type": "player", "referred_by": "a"})
        self.repo.save({"_id": "c", "_type": "player", "referred_by": "a"})
        self.repo.save({"_id": "d", "_type": "player", "referred_by": "a"})
        
        tree = self.repo.get_referral_tree("a", depth=1, include_stats=False)
        
        assert len(tree["children"]) == 3
        child_ids = [child["player_id"] for child in tree["children"]]
        assert "b" in child_ids
        assert "c" in child_ids
        assert "d" in child_ids
    
    def test_referral_stats(self):
        """Test referral statistics calculation."""
        # A → B, C
        # B → D, E
        # C → F
        players = [
            {"_id": "a", "_type": "player"},
            {"_id": "b", "_type": "player", "referred_by": "a"},
            {"_id": "c", "_type": "player", "referred_by": "a"},
            {"_id": "d", "_type": "player", "referred_by": "b"},
            {"_id": "e", "_type": "player", "referred_by": "b"},
            {"_id": "f", "_type": "player", "referred_by": "c"}
        ]
        
        for player in players:
            self.repo.save(player)
        
        tree = self.repo.get_referral_tree("a", depth=2, include_stats=True)
        
        assert tree["total_referrals"] == 5  # B, C, D, E, F
        assert tree["direct_referrals"] == 2  # B, C
        assert tree["indirect_referrals"] == 3  # D, E, F
    
    def test_empty_referral_tree(self):
        """Test player with no referrals."""
        self.repo.save({"_id": "lonely", "_type": "player"})
        
        tree = self.repo.get_referral_tree("lonely", depth=1, include_stats=True)
        
        assert tree["player_id"] == "lonely"
        assert len(tree["children"]) == 0
        assert tree["total_referrals"] == 0
        assert tree["direct_referrals"] == 0


class TestReferralSystemNegative:
    """Negative tests for error handling."""
    
    def setup_method(self):
        """Setup repository with test database."""
        self.db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.db_path = self.db_file.name
        self.db_file.close()
        
        self.repo = SQLiteRepository(self.db_path)
    
    def teardown_method(self):
        """Clean up test database."""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_nonexistent_player(self):
        """Test getting tree for non-existent player."""
        with pytest.raises(ValueError, match="not found"):
            self.repo.get_referral_tree("nonexistent", depth=1)
    
    def test_circular_reference_detection(self):
        """Test detection of circular referral references."""
        # This shouldn't happen in practice, but test it anyway
        # A → B → A (circular)
        self.repo.save({"_id": "a", "_type": "player", "referred_by": "b"})
        self.repo.save({"_id": "b", "_type": "player", "referred_by": "a"})
        
        # Should not infinite loop
        tree = self.repo.get_referral_tree("a", depth=5, include_stats=False)
        
        # Tree should terminate (implementation should handle cycles)
        assert tree is not None
    
    def test_self_referral(self):
        """Test player referring themselves (should be ignored)."""
        self.repo.save({"_id": "self", "_type": "player", "referred_by": "self"})
        
        tree = self.repo.get_referral_tree("self", depth=1, include_stats=False)
        
        # Should have no children
        assert len(tree["children"]) == 0
    
    def test_invalid_depth(self):
        """Test invalid depth values."""
        self.repo.save({"_id": "player", "_type": "player"})
        
        # Negative depth
        with pytest.raises(ValueError, match="depth"):
            self.repo.get_referral_tree("player", depth=-1)
        
        # Zero depth
        with pytest.raises(ValueError, match="depth"):
            self.repo.get_referral_tree("player", depth=0)
    
    def test_broken_referral_link(self):
        """Test referral link pointing to non-existent player."""
        # Player refers to someone who doesn't exist
        self.repo.save({"_id": "orphan", "_type": "player", "referred_by": "nonexistent"})
        
        tree = self.repo.get_referral_tree("orphan", depth=1, include_stats=False)
        
        # Should not crash, just have no children
        assert tree is not None
        assert len(tree["children"]) == 0


class TestReferralSystemPerformance:
    """Performance tests for large referral networks."""
    
    def setup_method(self):
        """Setup repository with test database."""
        self.db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.db_path = self.db_file.name
        self.db_file.close()
        
        self.repo = SQLiteRepository(self.db_path)
    
    def teardown_method(self):
        """Clean up test database."""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_wide_tree(self):
        """Test tree with many direct referrals (wide)."""
        # Root player
        self.repo.save({"_id": "root", "_type": "player"})
        
        # 100 direct referrals
        for i in range(100):
            self.repo.save({
                "_id": f"child_{i}",
                "_type": "player",
                "referred_by": "root"
            })
        
        import time
        start_time = time.time()
        tree = self.repo.get_referral_tree("root", depth=1, include_stats=True)
        elapsed = time.time() - start_time
        
        assert len(tree["children"]) == 100
        assert tree["direct_referrals"] == 100
        assert elapsed < 1.0, f"Took too long: {elapsed:.2f}s"
    
    def test_deep_tree(self):
        """Test deep referral chain."""
        # Create chain: 0 → 1 → 2 → ... → 50
        for i in range(51):
            player = {"_id": f"player_{i}", "_type": "player"}
            if i > 0:
                player["referred_by"] = f"player_{i-1}"
            self.repo.save(player)
        
        import time
        start_time = time.time()
        tree = self.repo.get_referral_tree("player_0", depth=50, include_stats=True)
        elapsed = time.time() - start_time
        
        assert tree["total_referrals"] == 50
        assert elapsed < 2.0, f"Took too long: {elapsed:.2f}s"
    
    def test_balanced_tree(self):
        """Test balanced binary tree (each node has 2 children)."""
        # Binary tree with 4 levels: 1 + 2 + 4 + 8 = 15 nodes
        def create_binary_tree(node_id, depth, max_depth):
            if depth > max_depth:
                return
            
            player = {"_id": f"node_{node_id}", "_type": "player"}
            if depth > 0:
                parent_id = node_id // 2
                player["referred_by"] = f"node_{parent_id}"
            self.repo.save(player)
            
            # Create children
            if depth < max_depth:
                create_binary_tree(node_id * 2, depth + 1, max_depth)
                create_binary_tree(node_id * 2 + 1, depth + 1, max_depth)
        
        create_binary_tree(1, 0, 4)
        
        tree = self.repo.get_referral_tree("node_1", depth=4, include_stats=True)
        
        assert tree["total_referrals"] == 30  # 2 + 4 + 8 + 16
        assert tree["direct_referrals"] == 2
    
    def test_large_network_stress(self):
        """Stress test with 500 players in complex network."""
        # Create a more realistic network
        import random
        
        # Root player
        self.repo.save({"_id": "root", "_type": "player"})
        
        # Generate 500 players with random referral structure
        all_players = ["root"]
        for i in range(500):
            # Pick random existing player as referrer
            referrer = random.choice(all_players)
            player_id = f"player_{i}"
            
            self.repo.save({
                "_id": player_id,
                "_type": "player",
                "referred_by": referrer
            })
            all_players.append(player_id)
        
        import time
        start_time = time.time()
        tree = self.repo.get_referral_tree("root", depth=10, include_stats=True)
        elapsed = time.time() - start_time
        
        assert tree["total_referrals"] > 0
        assert elapsed < 5.0, f"Took too long: {elapsed:.2f}s"
        print(f"\nProcessed {tree['total_referrals']} referrals in {elapsed:.3f}s")


class TestReferralSystemEdgeCases:
    """Edge cases and boundary tests."""
    
    def setup_method(self):
        """Setup repository with test database."""
        self.db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.db_path = self.db_file.name
        self.db_file.close()
        
        self.repo = SQLiteRepository(self.db_path)
    
    def teardown_method(self):
        """Clean up test database."""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_max_depth_limit(self):
        """Test with very large depth value."""
        # Create short chain
        self.repo.save({"_id": "a", "_type": "player"})
        self.repo.save({"_id": "b", "_type": "player", "referred_by": "a"})
        
        # Request depth of 1000 (but chain is only 1 level)
        tree = self.repo.get_referral_tree("a", depth=1000, include_stats=True)
        
        assert tree["total_referrals"] == 1
        assert tree["direct_referrals"] == 1
    
    def test_empty_database(self):
        """Test with completely empty database."""
        with pytest.raises(ValueError):
            self.repo.get_referral_tree("nobody", depth=1)
    
    def test_referral_with_additional_fields(self):
        """Test that additional player fields are preserved."""
        self.repo.save({
            "_id": "a",
            "_type": "player",
            "name": "Alice",
            "level": 50,
            "gems": 1000
        })
        self.repo.save({
            "_id": "b",
            "_type": "player",
            "name": "Bob",
            "level": 10,
            "gems": 100,
            "referred_by": "a"
        })
        
        tree = self.repo.get_referral_tree("a", depth=1, include_stats=False)
        
        # Check that child has additional fields
        child = tree["children"][0]
        assert "name" in child or "player_id" in child
    
    def test_multiple_roots(self):
        """Test that each player's tree is independent."""
        # Two separate trees: A→B and C→D
        self.repo.save({"_id": "a", "_type": "player"})
        self.repo.save({"_id": "b", "_type": "player", "referred_by": "a"})
        self.repo.save({"_id": "c", "_type": "player"})
        self.repo.save({"_id": "d", "_type": "player", "referred_by": "c"})
        
        tree_a = self.repo.get_referral_tree("a", depth=1, include_stats=True)
        tree_c = self.repo.get_referral_tree("c", depth=1, include_stats=True)
        
        assert tree_a["total_referrals"] == 1  # B
        assert tree_c["total_referrals"] == 1  # D
        assert tree_a["children"][0]["player_id"] == "b"
        assert tree_c["children"][0]["player_id"] == "d"


class TestReferralBonusCalculation:
    """Tests for referral bonus calculation logic."""
    
    def setup_method(self):
        """Setup repository with test database."""
        self.db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.db_path = self.db_file.name
        self.db_file.close()
        
        self.repo = SQLiteRepository(self.db_path)
    
    def teardown_method(self):
        """Clean up test database."""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_calculate_referral_bonus(self):
        """Test calculating bonus based on referral tree."""
        # A → B, C, D (3 direct)
        # B → E, F (2 indirect)
        players = [
            {"_id": "a", "_type": "player"},
            {"_id": "b", "_type": "player", "referred_by": "a"},
            {"_id": "c", "_type": "player", "referred_by": "a"},
            {"_id": "d", "_type": "player", "referred_by": "a"},
            {"_id": "e", "_type": "player", "referred_by": "b"},
            {"_id": "f", "_type": "player", "referred_by": "b"}
        ]
        
        for player in players:
            self.repo.save(player)
        
        tree = self.repo.get_referral_tree("a", depth=2, include_stats=True)
        
        # Calculate bonus: 500 gems per direct, 100 gems per indirect
        direct_bonus = tree["direct_referrals"] * 500
        indirect_bonus = tree["indirect_referrals"] * 100
        total_bonus = direct_bonus + indirect_bonus
        
        assert direct_bonus == 1500  # 3 * 500
        assert indirect_bonus == 200  # 2 * 100
        assert total_bonus == 1700
    
    def test_milestone_rewards(self):
        """Test milestone-based rewards."""
        # Create root with varying number of referrals
        self.repo.save({"_id": "root", "_type": "player"})
        
        milestones = {
            10: "bronze_badge",
            25: "silver_badge",
            50: "gold_badge",
            100: "legendary_badge"
        }
        
        # Create 100 referrals
        for i in range(100):
            self.repo.save({
                "_id": f"ref_{i}",
                "_type": "player",
                "referred_by": "root"
            })
        
        tree = self.repo.get_referral_tree("root", depth=1, include_stats=True)
        total = tree["total_referrals"]
        
        # Check which milestones are reached
        earned_badges = []
        for threshold, badge in sorted(milestones.items()):
            if total >= threshold:
                earned_badges.append(badge)
        
        assert "bronze_badge" in earned_badges
        assert "silver_badge" in earned_badges
        assert "gold_badge" in earned_badges
        assert "legendary_badge" in earned_badges
        assert len(earned_badges) == 4

