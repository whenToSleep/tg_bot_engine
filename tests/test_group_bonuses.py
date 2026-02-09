"""Tests for Group Bonus System (Synergies)."""

import pytest
from engine.core.group_bonuses import (
    GroupBonusCalculator,
    SynergyRule,
    create_element_synergy_rule,
    create_rarity_synergy_rule,
    analyze_deck_composition
)
from engine.core.modifiers import StatCalculator, ModifierType


class TestGroupBonusCalculator:
    """Tests for GroupBonusCalculator."""
    
    def test_basic_synergy(self):
        """Test basic synergy activation."""
        rule = SynergyRule(
            synergy_id="fire_3",
            name="Fire Synergy",
            description="+15% ATK",
            condition={"element": "fire", "min_count": 3},
            bonuses=[{"stat": "atk", "type": "percent", "value": 15}]
        )
        
        calculator = GroupBonusCalculator([rule])
        
        # 3 fire cards - should activate
        deck = [
            {"element": "fire"},
            {"element": "fire"},
            {"element": "fire"}
        ]
        
        result = calculator.calculate(deck)
        assert result["fire_3"]["active"] is True
        assert result["fire_3"]["matching_count"] == 3
        assert len(result["fire_3"]["bonuses"]) == 1
    
    def test_synergy_not_active(self):
        """Test synergy not activating with insufficient count."""
        rule = SynergyRule(
            synergy_id="fire_3",
            name="Fire Synergy",
            description="+15% ATK",
            condition={"element": "fire", "min_count": 3},
            bonuses=[{"stat": "atk", "type": "percent", "value": 15}]
        )
        
        calculator = GroupBonusCalculator([rule])
        
        # Only 2 fire cards - should not activate
        deck = [
            {"element": "fire"},
            {"element": "fire"},
            {"element": "water"}
        ]
        
        result = calculator.calculate(deck)
        assert result["fire_3"]["active"] is False
        assert result["fire_3"]["matching_count"] == 2
        assert len(result["fire_3"]["bonuses"]) == 0
    
    def test_multiple_synergies(self):
        """Test multiple synergies activating simultaneously."""
        rules = [
            SynergyRule(
                synergy_id="fire_3",
                name="Fire Synergy",
                description="+15% ATK",
                condition={"element": "fire", "min_count": 3},
                bonuses=[{"stat": "atk", "type": "percent", "value": 15}]
            ),
            SynergyRule(
                synergy_id="rare_2",
                name="Rare Synergy",
                description="+10% DEF",
                condition={"rarity": "S", "min_count": 2},
                bonuses=[{"stat": "def", "type": "percent", "value": 10}]
            )
        ]
        
        calculator = GroupBonusCalculator(rules)
        
        deck = [
            {"element": "fire", "rarity": "S"},
            {"element": "fire", "rarity": "S"},
            {"element": "fire", "rarity": "C"}
        ]
        
        result = calculator.calculate(deck)
        assert result["fire_3"]["active"] is True
        assert result["rare_2"]["active"] is True
    
    def test_synergy_from_dict(self):
        """Test creating synergy from dictionary."""
        rule_dict = {
            "id": "water_4",
            "name": "Water Mastery",
            "description": "+20% DEF",
            "condition": {"element": "water", "min_count": 4},
            "bonus": {"stat": "def", "type": "percent", "value": 20}
        }
        
        calculator = GroupBonusCalculator([rule_dict])
        
        deck = [
            {"element": "water"},
            {"element": "water"},
            {"element": "water"},
            {"element": "water"}
        ]
        
        result = calculator.calculate(deck)
        assert result["water_4"]["active"] is True
    
    def test_get_active_bonuses(self):
        """Test getting all active bonuses."""
        rules = [
            SynergyRule(
                synergy_id="fire_3",
                name="Fire",
                description="",
                condition={"element": "fire", "min_count": 3},
                bonuses=[
                    {"stat": "atk", "type": "percent", "value": 15},
                    {"stat": "spd", "type": "flat", "value": 5}
                ]
            ),
            SynergyRule(
                synergy_id="water_3",
                name="Water",
                description="",
                condition={"element": "water", "min_count": 3},
                bonuses=[{"stat": "def", "type": "percent", "value": 20}]
            )
        ]
        
        calculator = GroupBonusCalculator(rules)
        
        deck = [
            {"element": "fire"},
            {"element": "fire"},
            {"element": "fire"}
        ]
        
        bonuses = calculator.get_active_bonuses(deck)
        assert len(bonuses) == 2  # 2 bonuses from fire synergy
        assert bonuses[0]["stat"] == "atk"
        assert bonuses[1]["stat"] == "spd"
    
    def test_priority_ordering(self):
        """Test that higher priority synergies are calculated first."""
        rules = [
            SynergyRule(
                synergy_id="low_priority",
                name="Low",
                description="",
                condition={"element": "fire", "min_count": 2},
                bonuses=[{"stat": "atk", "type": "flat", "value": 10}],
                priority=0
            ),
            SynergyRule(
                synergy_id="high_priority",
                name="High",
                description="",
                condition={"element": "fire", "min_count": 2},
                bonuses=[{"stat": "atk", "type": "flat", "value": 20}],
                priority=10
            )
        ]
        
        calculator = GroupBonusCalculator(rules)
        
        # Check that rules are sorted by priority
        assert calculator.rules[0].synergy_id == "high_priority"
        assert calculator.rules[1].synergy_id == "low_priority"


class TestSynergyFactories:
    """Tests for synergy factory functions."""
    
    def test_create_element_synergy(self):
        """Test element synergy factory."""
        rule = create_element_synergy_rule(
            element="fire",
            min_count=3,
            bonus_stat="atk",
            bonus_value=15,
            bonus_type="percent"
        )
        
        assert rule.synergy_id == "fire_synergy_3"
        assert rule.name == "Fire Resonance"
        assert "+15% ATK" in rule.description
        assert rule.condition == {"element": "fire", "min_count": 3}
        assert len(rule.bonuses) == 1
        assert rule.bonuses[0]["stat"] == "atk"
    
    def test_create_rarity_synergy(self):
        """Test rarity synergy factory."""
        rule = create_rarity_synergy_rule(
            rarity="S",
            min_count=3,
            bonus_stats=["atk", "def", "hp"],
            bonus_value=10,
            bonus_type="percent"
        )
        
        assert rule.synergy_id == "rarity_S_3"
        assert rule.name == "S-Rank Assembly"
        assert rule.condition == {"rarity": "S", "min_count": 3}
        assert len(rule.bonuses) == 3
        
        stat_names = [b["stat"] for b in rule.bonuses]
        assert "atk" in stat_names
        assert "def" in stat_names
        assert "hp" in stat_names


class TestIntegrationWithStatCalculator:
    """Integration tests with StatCalculator."""
    
    def test_apply_synergy_to_entity(self):
        """Test applying synergies to entity."""
        rule = SynergyRule(
            synergy_id="fire_3",
            name="Fire Synergy",
            description="+15% ATK",
            condition={"element": "fire", "min_count": 3},
            bonuses=[{"stat": "attack", "type": "percent", "value": 15}]
        )
        
        calculator = GroupBonusCalculator([rule])
        
        deck = [
            {"element": "fire"},
            {"element": "fire"},
            {"element": "fire"}
        ]
        
        # Create entity
        entity = {
            "base_attack": 100,
            "modifiers": []
        }
        
        # Apply synergies
        calculator.apply_to_entity(deck, entity)
        
        # Check that synergy was applied
        final_stats = StatCalculator.get_all_stats(entity)
        assert abs(final_stats["attack"] - 115) < 0.01  # 100 * 1.15
    
    def test_multiple_synergy_stacking(self):
        """Test multiple synergies stacking on same stat."""
        rules = [
            SynergyRule(
                synergy_id="fire_3",
                name="Fire",
                description="",
                condition={"element": "fire", "min_count": 3},
                bonuses=[{"stat": "attack", "type": "percent", "value": 15}]
            ),
            SynergyRule(
                synergy_id="rare_2",
                name="Rare",
                description="",
                condition={"rarity": "S", "min_count": 2},
                bonuses=[{"stat": "attack", "type": "percent", "value": 10}]
            )
        ]
        
        calculator = GroupBonusCalculator(rules)
        
        deck = [
            {"element": "fire", "rarity": "S"},
            {"element": "fire", "rarity": "S"},
            {"element": "fire", "rarity": "C"}
        ]
        
        entity = {
            "base_attack": 100,
            "modifiers": []
        }
        
        calculator.apply_to_entity(deck, entity)
        
        final_stats = StatCalculator.get_all_stats(entity)
        # 100 * (1 + 0.15 + 0.10) = 100 * 1.25 = 125
        assert final_stats["attack"] == 125


class TestDeckCompositionAnalysis:
    """Tests for deck composition analysis."""
    
    def test_analyze_basic_deck(self):
        """Test basic deck analysis."""
        deck = [
            {"element": "fire", "rarity": "C"},
            {"element": "fire", "rarity": "S"},
            {"element": "water", "rarity": "B"},
            {"element": "water", "rarity": "A"}
        ]
        
        stats = analyze_deck_composition(deck)
        
        assert stats["total_count"] == 4
        assert stats["elements"]["fire"] == 2
        assert stats["elements"]["water"] == 2
        assert stats["rarities"]["C"] == 1
        assert stats["rarities"]["S"] == 1
        assert stats["rarities"]["B"] == 1
        assert stats["rarities"]["A"] == 1
    
    def test_analyze_homogeneous_deck(self):
        """Test analysis of homogeneous deck."""
        deck = [
            {"element": "fire", "rarity": "S"},
            {"element": "fire", "rarity": "S"},
            {"element": "fire", "rarity": "S"}
        ]
        
        stats = analyze_deck_composition(deck)
        
        assert stats["total_count"] == 3
        assert stats["elements"]["fire"] == 3
        assert stats["rarities"]["S"] == 3
        assert stats["most_common_element"][0] == "fire"
        assert stats["most_common_element"][1] == 3
        assert stats["most_common_rarity"][0] == "S"
    
    def test_analyze_empty_deck(self):
        """Test analysis of empty deck."""
        deck = []
        
        stats = analyze_deck_composition(deck)
        
        assert stats["total_count"] == 0
        assert stats["elements"] == {}
        assert stats["rarities"] == {}
        assert stats["most_common_element"] is None


class TestEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_exact_count_match(self):
        """Test synergy activating at exact threshold."""
        rule = SynergyRule(
            synergy_id="fire_3",
            name="Fire",
            description="",
            condition={"element": "fire", "min_count": 3},
            bonuses=[{"stat": "atk", "type": "flat", "value": 10}]
        )
        
        calculator = GroupBonusCalculator([rule])
        
        # Exactly 3 fire cards
        deck = [
            {"element": "fire"},
            {"element": "fire"},
            {"element": "fire"}
        ]
        
        result = calculator.calculate(deck)
        assert result["fire_3"]["active"] is True
    
    def test_duplicate_cards(self):
        """Test synergies work with duplicate cards."""
        rule = SynergyRule(
            synergy_id="fire_4",
            name="Fire",
            description="",
            condition={"element": "fire", "min_count": 4},
            bonuses=[{"stat": "atk", "type": "flat", "value": 10}]
        )
        
        calculator = GroupBonusCalculator([rule])
        
        # 4 identical fire cards
        deck = [
            {"id": "fireball_1", "element": "fire"},
            {"id": "fireball_1", "element": "fire"},
            {"id": "fireball_1", "element": "fire"},
            {"id": "fireball_1", "element": "fire"}
        ]
        
        result = calculator.calculate(deck)
        assert result["fire_4"]["active"] is True
        assert result["fire_4"]["matching_count"] == 4
    
    def test_empty_deck(self):
        """Test synergies with empty deck."""
        rule = SynergyRule(
            synergy_id="fire_3",
            name="Fire",
            description="",
            condition={"element": "fire", "min_count": 3},
            bonuses=[{"stat": "atk", "type": "flat", "value": 10}]
        )
        
        calculator = GroupBonusCalculator([rule])
        
        result = calculator.calculate([])
        assert result["fire_3"]["active"] is False
        assert result["fire_3"]["matching_count"] == 0
    
    def test_mixed_elements_complex(self):
        """Test complex deck with mixed elements."""
        rules = [
            SynergyRule(
                synergy_id="fire_3",
                name="Fire",
                description="",
                condition={"element": "fire", "min_count": 3},
                bonuses=[{"stat": "atk", "type": "percent", "value": 15}]
            ),
            SynergyRule(
                synergy_id="water_3",
                name="Water",
                description="",
                condition={"element": "water", "min_count": 3},
                bonuses=[{"stat": "def", "type": "percent", "value": 20}]
            ),
            SynergyRule(
                synergy_id="fire_water_balance",
                name="Balance",
                description="",
                condition={"min_count": 6},  # No specific element
                bonuses=[{"stat": "hp", "type": "percent", "value": 10}]
            )
        ]
        
        calculator = GroupBonusCalculator(rules)
        
        deck = [
            {"element": "fire"},
            {"element": "fire"},
            {"element": "fire"},
            {"element": "water"},
            {"element": "water"},
            {"element": "water"}
        ]
        
        result = calculator.calculate(deck)
        assert result["fire_3"]["active"] is True
        assert result["water_3"]["active"] is True
        assert result["fire_water_balance"]["active"] is True

