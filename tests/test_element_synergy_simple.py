"""Simplified tests for Element Synergy compatible with existing API.

Tests the actual GroupBonusCalculator implementation.
"""

import pytest
from engine.core.group_bonuses import (
    GroupBonusCalculator,
    SynergyRule,
    analyze_deck_composition
)


class TestGroupBonusCalculatorBasic:
    """Basic tests for GroupBonusCalculator."""
    
    def test_simple_synergy(self):
        """Test basic synergy rule."""
        rule = SynergyRule(
            synergy_id="fire_synergy",
            name="Fire Synergy",
            description="+20% attack",
            condition={"element": "fire", "min_count": 3},
            bonuses=[{"stat": "atk", "type": "percent", "value": 20}]
        )
        
        calculator = GroupBonusCalculator([rule])
        
        deck = [
            {"element": "fire"},
            {"element": "fire"},
            {"element": "fire"}
        ]
        
        result = calculator.calculate(deck)
        
        assert "fire_synergy" in result
        assert result["fire_synergy"]["active"] is True
    
    def test_synergy_not_active(self):
        """Test synergy not activated when condition not met."""
        rule = SynergyRule(
            synergy_id="fire_synergy",
            name="Fire Synergy",
            description="+20% attack",
            condition={"element": "fire", "min_count": 3},
            bonuses=[{"stat": "atk", "type": "percent", "value": 20}]
        )
        
        calculator = GroupBonusCalculator([rule])
        
        # Only 2 fire cards
        deck = [
            {"element": "fire"},
            {"element": "fire"},
            {"element": "water"}
        ]
        
        result = calculator.calculate(deck)
        
        assert result["fire_synergy"]["active"] is False
    
    def test_multiple_synergies(self):
        """Test multiple synergies."""
        rules = [
            SynergyRule(
                synergy_id="fire_synergy",
                name="Fire Synergy",
                description="+20% attack",
                condition={"element": "fire", "min_count": 3},
                bonuses=[{"stat": "atk", "type": "percent", "value": 20}]
            ),
            SynergyRule(
                synergy_id="water_synergy",
                name="Water Synergy",
                description="+15% defense",
                condition={"element": "water", "min_count": 3},
                bonuses=[{"stat": "def", "type": "percent", "value": 15}]
            )
        ]
        
        calculator = GroupBonusCalculator(rules)
        
        deck = [
            {"element": "fire"}, {"element": "fire"}, {"element": "fire"},
            {"element": "water"}, {"element": "water"}, {"element": "water"}
        ]
        
        result = calculator.calculate(deck)
        
        assert result["fire_synergy"]["active"] is True
        assert result["water_synergy"]["active"] is True
    
    def test_empty_deck(self):
        """Test with empty deck."""
        rule = SynergyRule(
            synergy_id="fire_synergy",
            name="Fire Synergy",
            description="+20% attack",
            condition={"element": "fire", "min_count": 3},
            bonuses=[{"stat": "atk", "type": "percent", "value": 20}]
        )
        
        calculator = GroupBonusCalculator([rule])
        
        result = calculator.calculate([])
        
        assert result["fire_synergy"]["active"] is False


class TestDeckCompositionAnalysis:
    """Tests for deck composition analysis."""
    
    def test_analyze_composition(self):
        """Test analyzing deck composition."""
        deck = [
            {"element": "fire", "rarity": "S"},
            {"element": "fire", "rarity": "A"},
            {"element": "water", "rarity": "B"}
        ]
        
        stats = analyze_deck_composition(deck)
        
        assert stats["total_count"] == 3
        assert stats["elements"]["fire"] == 2
        assert stats["elements"]["water"] == 1
        assert stats["rarities"]["S"] == 1
        assert stats["rarities"]["A"] == 1
        assert stats["rarities"]["B"] == 1
    
    def test_empty_composition(self):
        """Test analyzing empty deck."""
        stats = analyze_deck_composition([])
        
        assert stats["total_count"] == 0
        assert stats["elements"] == {}
        assert stats["most_common_element"] is None


class TestPerformance:
    """Performance tests."""
    
    def test_large_deck(self):
        """Test with large deck."""
        rule = SynergyRule(
            synergy_id="fire_synergy",
            name="Fire Synergy",
            description="+20% attack",
            condition={"element": "fire", "min_count": 3},
            bonuses=[{"stat": "atk", "type": "percent", "value": 20}]
        )
        
        calculator = GroupBonusCalculator([rule])
        
        # Large deck with 100 cards
        deck = [{"element": "fire"} for _ in range(100)]
        
        import time
        start = time.time()
        result = calculator.calculate(deck)
        elapsed = time.time() - start
        
        assert result["fire_synergy"]["active"] is True
        assert elapsed < 0.1  # Should be fast
    
    def test_many_rules(self):
        """Test with many rules."""
        rules = []
        for i in range(50):
            rules.append(SynergyRule(
                synergy_id=f"rule_{i}",
                name=f"Rule {i}",
                description="Test",
                condition={"element": "fire", "min_count": 1},
                bonuses=[{"stat": "atk", "type": "flat", "value": 1}]
            ))
        
        calculator = GroupBonusCalculator(rules)
        
        deck = [{"element": "fire"}] * 10
        
        import time
        start = time.time()
        result = calculator.calculate(deck)
        elapsed = time.time() - start
        
        assert elapsed < 0.5  # Should be reasonably fast

