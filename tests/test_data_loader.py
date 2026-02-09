"""Tests for DataLoader functionality.

Tests loading JSON data, schema validation, and error handling.
"""

import pytest
import json
import tempfile
from pathlib import Path
from engine.core.data_loader import (
    DataLoader,
    DataLoaderError,
    SchemaNotFoundError,
    DataValidationError,
    get_global_loader,
    reset_global_loader,
)


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create temporary data directory structure."""
    # Create directories
    (tmp_path / "schemas").mkdir()
    (tmp_path / "mobs").mkdir()
    (tmp_path / "items").mkdir()
    
    # Create simple schema
    schema = {
        "type": "object",
        "required": ["id", "name"],
        "properties": {
            "id": {"type": "string"},
            "name": {"type": "string"},
            "value": {"type": "integer"}
        }
    }
    
    schema_path = tmp_path / "schemas" / "test_schema.json"
    with open(schema_path, 'w') as f:
        json.dump(schema, f)
    
    # Create valid test data
    test_data = {"id": "test_1", "name": "Test Item", "value": 100}
    data_path = tmp_path / "mobs" / "test_mob.json"
    with open(data_path, 'w') as f:
        json.dump(test_data, f)
    
    return tmp_path


class TestDataLoader:
    """Tests for DataLoader class."""
    
    def test_init(self, temp_data_dir):
        """Test DataLoader initialization."""
        loader = DataLoader(str(temp_data_dir))
        
        assert loader.data_dir == temp_data_dir
        assert loader.schemas == {}
        assert loader.data == {}
    
    def test_load_schema_success(self, temp_data_dir):
        """Test successful schema loading."""
        loader = DataLoader(str(temp_data_dir))
        
        schema = loader.load_schema("test_schema.json")
        
        assert schema["type"] == "object"
        assert "id" in schema["required"]
    
    def test_load_schema_not_found(self, temp_data_dir):
        """Test loading nonexistent schema."""
        loader = DataLoader(str(temp_data_dir))
        
        with pytest.raises(SchemaNotFoundError, match="Schema not found"):
            loader.load_schema("nonexistent.json")
    
    def test_validate_data_success(self, temp_data_dir):
        """Test successful data validation."""
        loader = DataLoader(str(temp_data_dir))
        schema = loader.load_schema("test_schema.json")
        
        valid_data = {"id": "test", "name": "Test", "value": 42}
        
        # Should not raise
        loader.validate_data(valid_data, schema)
    
    def test_validate_data_failure(self, temp_data_dir):
        """Test data validation failure."""
        loader = DataLoader(str(temp_data_dir))
        schema = loader.load_schema("test_schema.json")
        
        invalid_data = {"id": "test"}  # Missing required 'name'
        
        with pytest.raises(DataValidationError, match="Validation failed"):
            loader.validate_data(invalid_data, schema)
    
    def test_load_json_file_success(self, temp_data_dir):
        """Test loading JSON file."""
        loader = DataLoader(str(temp_data_dir))
        
        file_path = temp_data_dir / "mobs" / "test_mob.json"
        data = loader.load_json_file(file_path)
        
        assert data["id"] == "test_1"
        assert data["name"] == "Test Item"
    
    def test_load_json_file_invalid(self, temp_data_dir):
        """Test loading invalid JSON."""
        loader = DataLoader(str(temp_data_dir))
        
        # Create invalid JSON file
        invalid_path = temp_data_dir / "mobs" / "invalid.json"
        with open(invalid_path, 'w') as f:
            f.write("{invalid json")
        
        with pytest.raises(DataValidationError, match="Invalid JSON"):
            loader.load_json_file(invalid_path)
    
    def test_load_category_success(self, temp_data_dir):
        """Test loading category with validation."""
        loader = DataLoader(str(temp_data_dir))
        
        mobs = loader.load_category("mobs", "test_schema.json")
        
        assert "test_1" in mobs
        assert mobs["test_1"]["name"] == "Test Item"
        assert loader.is_loaded("mobs")
    
    def test_load_category_no_validation(self, temp_data_dir):
        """Test loading category without validation."""
        loader = DataLoader(str(temp_data_dir))
        
        mobs = loader.load_category("mobs", "test_schema.json", validate_schema=False)
        
        assert "test_1" in mobs
    
    def test_load_category_missing_directory(self, temp_data_dir):
        """Test loading from nonexistent directory."""
        loader = DataLoader(str(temp_data_dir))
        
        with pytest.raises(DataLoaderError, match="Category directory not found"):
            loader.load_category("nonexistent", "test_schema.json")
    
    def test_load_category_duplicate_ids(self, temp_data_dir):
        """Test loading category with duplicate IDs."""
        loader = DataLoader(str(temp_data_dir))
        
        # Create duplicate ID
        duplicate_data = {"id": "test_1", "name": "Duplicate", "value": 200}
        duplicate_path = temp_data_dir / "mobs" / "duplicate.json"
        with open(duplicate_path, 'w') as f:
            json.dump(duplicate_data, f)
        
        with pytest.raises(DataValidationError, match="Duplicate ID"):
            loader.load_category("mobs", "test_schema.json")
    
    def test_load_category_missing_id(self, temp_data_dir):
        """Test loading data without ID field."""
        loader = DataLoader(str(temp_data_dir))
        
        # Create data without ID
        no_id_data = {"name": "No ID", "value": 300}
        no_id_path = temp_data_dir / "items" / "no_id.json"
        with open(no_id_path, 'w') as f:
            json.dump(no_id_data, f)
        
        with pytest.raises(DataValidationError, match="Missing 'id' field"):
            loader.load_category("items", "test_schema.json", validate_schema=False)
    
    def test_get_success(self, temp_data_dir):
        """Test getting item from loaded category."""
        loader = DataLoader(str(temp_data_dir))
        loader.load_category("mobs", "test_schema.json")
        
        item = loader.get("mobs", "test_1")
        
        assert item is not None
        assert item["name"] == "Test Item"
    
    def test_get_not_found(self, temp_data_dir):
        """Test getting nonexistent item."""
        loader = DataLoader(str(temp_data_dir))
        loader.load_category("mobs", "test_schema.json")
        
        item = loader.get("mobs", "nonexistent")
        
        assert item is None
    
    def test_get_category_not_loaded(self, temp_data_dir):
        """Test getting from unloaded category."""
        loader = DataLoader(str(temp_data_dir))
        
        with pytest.raises(DataLoaderError, match="not loaded"):
            loader.get("mobs", "test_1")
    
    def test_get_all(self, temp_data_dir):
        """Test getting all items from category."""
        loader = DataLoader(str(temp_data_dir))
        loader.load_category("mobs", "test_schema.json")
        
        all_items = loader.get_all("mobs")
        
        assert len(all_items) == 1
        assert "test_1" in all_items
    
    def test_is_loaded(self, temp_data_dir):
        """Test checking if category is loaded."""
        loader = DataLoader(str(temp_data_dir))
        
        assert not loader.is_loaded("mobs")
        
        loader.load_category("mobs", "test_schema.json")
        
        assert loader.is_loaded("mobs")
    
    def test_reload_category(self, temp_data_dir):
        """Test reloading category."""
        loader = DataLoader(str(temp_data_dir))
        loader.load_category("mobs", "test_schema.json")
        
        # Modify data
        new_data = {"id": "test_2", "name": "New Item", "value": 500}
        new_path = temp_data_dir / "mobs" / "test_2.json"
        with open(new_path, 'w') as f:
            json.dump(new_data, f)
        
        # Reload
        reloaded = loader.reload_category("mobs", "test_schema.json")
        
        assert "test_2" in reloaded
        assert len(reloaded) == 2
    
    def test_get_stats(self, temp_data_dir):
        """Test getting loader statistics."""
        loader = DataLoader(str(temp_data_dir))
        
        stats = loader.get_stats()
        assert stats["total_items"] == 0
        assert stats["schemas_cached"] == 0
        
        loader.load_category("mobs", "test_schema.json")
        
        stats = loader.get_stats()
        assert stats["total_items"] == 1
        assert stats["schemas_cached"] == 1
        assert "mobs" in stats["loaded_categories"]


class TestGlobalLoader:
    """Tests for global loader singleton."""
    
    def test_get_global_loader(self):
        """Test getting global loader instance."""
        reset_global_loader()
        
        loader1 = get_global_loader()
        loader2 = get_global_loader()
        
        # Should be same instance
        assert loader1 is loader2
    
    def test_reset_global_loader(self):
        """Test resetting global loader."""
        loader1 = get_global_loader()
        reset_global_loader()
        loader2 = get_global_loader()
        
        # Should be different instances
        assert loader1 is not loader2


class TestRealData:
    """Tests with real project data files."""
    
    def test_load_real_mobs(self):
        """Test loading real mob data from project."""
        loader = DataLoader("data")
        
        try:
            mobs = loader.load_category("mobs", "mob_schema.json")
            
            # Check that we loaded some mobs
            assert len(mobs) > 0
            
            # Check goblin warrior exists
            if "goblin_warrior" in mobs:
                goblin = mobs["goblin_warrior"]
                assert goblin["name"] == "Goblin Warrior"
                assert goblin["hp"] > 0
                assert goblin["attack"] > 0
        except (DataLoaderError, FileNotFoundError):
            pytest.skip("Real data files not available")
    
    def test_load_real_items(self):
        """Test loading real item data from project."""
        loader = DataLoader("data")
        
        try:
            items = loader.load_category("items", "item_schema.json")
            
            # Check that we loaded some items
            assert len(items) > 0
            
            # Check health potion exists
            if "health_potion_small" in items:
                potion = items["health_potion_small"]
                assert potion["name"] == "Small Health Potion"
                assert potion["type"] == "consumable"
        except (DataLoaderError, FileNotFoundError):
            pytest.skip("Real data files not available")

