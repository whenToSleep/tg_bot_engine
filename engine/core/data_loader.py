"""Data loader module - JSON content loading and validation.

Provides data-driven game development by loading game content
from JSON files with JSON Schema validation.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from jsonschema import validate, ValidationError as JsonValidationError


class DataLoaderError(Exception):
    """Base exception for data loader errors."""
    pass


class SchemaNotFoundError(DataLoaderError):
    """Raised when schema file is not found."""
    pass


class DataValidationError(DataLoaderError):
    """Raised when data doesn't match schema."""
    pass


class DataLoader:
    """Loader and validator for game data from JSON files.
    
    Loads game content (mobs, items, effects) from JSON files
    and validates them against JSON schemas.
    
    Example:
        >>> loader = DataLoader("data")
        >>> mobs = loader.load_category("mobs", "mob_schema.json")
        >>> goblin = loader.get("mobs", "goblin_warrior")
    """
    
    def __init__(self, data_dir: str = "data") -> None:
        """Initialize data loader.
        
        Args:
            data_dir: Root directory for data files
        """
        self.data_dir = Path(data_dir)
        self.schemas: Dict[str, dict] = {}
        self.data: Dict[str, Dict[str, Any]] = {}
    
    def load_schema(self, schema_filename: str) -> dict:
        """Load JSON schema from schemas directory.
        
        Args:
            schema_filename: Schema file name (e.g., "mob_schema.json")
            
        Returns:
            Loaded schema as dictionary
            
        Raises:
            SchemaNotFoundError: If schema file doesn't exist
        """
        schema_path = self.data_dir / "schemas" / schema_filename
        
        if not schema_path.exists():
            raise SchemaNotFoundError(
                f"Schema not found: {schema_path}"
            )
        
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            return schema
        except json.JSONDecodeError as e:
            raise DataValidationError(
                f"Invalid JSON in schema {schema_filename}: {e}"
            )
    
    def validate_data(self, data: dict, schema: dict) -> None:
        """Validate data against schema.
        
        Args:
            data: Data to validate
            schema: JSON schema
            
        Raises:
            DataValidationError: If validation fails
        """
        try:
            validate(instance=data, schema=schema)
        except JsonValidationError as e:
            raise DataValidationError(
                f"Validation failed: {e.message} at {list(e.path)}"
            )
    
    def load_json_file(self, file_path: Path) -> dict:
        """Load single JSON file.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Loaded data
            
        Raises:
            DataValidationError: If JSON is invalid
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise DataValidationError(
                f"Invalid JSON in {file_path.name}: {e}"
            )
        except FileNotFoundError:
            raise DataLoaderError(f"File not found: {file_path}")
    
    def load_category(
        self, 
        category: str, 
        schema_filename: str,
        validate_schema: bool = True
    ) -> Dict[str, Any]:
        """Load all data files from a category with validation.
        
        Args:
            category: Category name (subdirectory name, e.g., "mobs")
            schema_filename: Schema file to use for validation
            validate_schema: Whether to validate against schema
            
        Returns:
            Dictionary mapping item IDs to their data
            
        Raises:
            DataLoaderError: If loading fails
            
        Example:
            >>> mobs = loader.load_category("mobs", "mob_schema.json")
            >>> print(mobs["goblin_warrior"]["name"])
            Goblin Warrior
        """
        # Load schema if validation enabled
        schema = None
        if validate_schema:
            if schema_filename not in self.schemas:
                self.schemas[schema_filename] = self.load_schema(schema_filename)
            schema = self.schemas[schema_filename]
        
        # Load all JSON files from category directory
        category_path = self.data_dir / category
        
        if not category_path.exists():
            raise DataLoaderError(
                f"Category directory not found: {category_path}"
            )
        
        loaded_data: Dict[str, Any] = {}
        
        for json_file in category_path.glob("*.json"):
            # Load JSON
            item_data = self.load_json_file(json_file)
            
            # Validate if schema provided
            if schema:
                self.validate_data(item_data, schema)
            
            # Check for ID field
            if 'id' not in item_data:
                raise DataValidationError(
                    f"Missing 'id' field in {json_file.name}"
                )
            
            item_id = item_data['id']
            
            # Check for duplicates
            if item_id in loaded_data:
                raise DataValidationError(
                    f"Duplicate ID '{item_id}' found in {json_file.name}"
                )
            
            loaded_data[item_id] = item_data
        
        # Cache loaded data
        self.data[category] = loaded_data
        
        return loaded_data
    
    def get(self, category: str, item_id: str) -> Optional[dict]:
        """Get specific item from loaded category.
        
        Args:
            category: Category name
            item_id: Item identifier
            
        Returns:
            Item data or None if not found
            
        Raises:
            DataLoaderError: If category not loaded
        """
        if category not in self.data:
            raise DataLoaderError(
                f"Category '{category}' not loaded. Call load_category() first."
            )
        
        return self.data[category].get(item_id)
    
    def get_all(self, category: str) -> Dict[str, Any]:
        """Get all items from category.
        
        Args:
            category: Category name
            
        Returns:
            Dictionary of all items
            
        Raises:
            DataLoaderError: If category not loaded
        """
        if category not in self.data:
            raise DataLoaderError(
                f"Category '{category}' not loaded. Call load_category() first."
            )
        
        return self.data[category]
    
    def is_loaded(self, category: str) -> bool:
        """Check if category is loaded.
        
        Args:
            category: Category name
            
        Returns:
            True if loaded, False otherwise
        """
        return category in self.data
    
    def reload_category(
        self, 
        category: str, 
        schema_filename: str
    ) -> Dict[str, Any]:
        """Reload category data (hot reload).
        
        Args:
            category: Category name
            schema_filename: Schema file name
            
        Returns:
            Reloaded data
        """
        # Clear cached schema
        if schema_filename in self.schemas:
            del self.schemas[schema_filename]
        
        # Clear cached data
        if category in self.data:
            del self.data[category]
        
        # Reload
        return self.load_category(category, schema_filename)
    
    def get_stats(self) -> dict:
        """Get loader statistics.
        
        Returns:
            Dictionary with loader stats
        """
        return {
            "loaded_categories": list(self.data.keys()),
            "total_items": sum(len(items) for items in self.data.values()),
            "schemas_cached": len(self.schemas),
        }


# Global singleton instance
_global_loader: Optional[DataLoader] = None


def get_global_loader(data_dir: str = "data") -> DataLoader:
    """Get or create global DataLoader instance.
    
    Args:
        data_dir: Data directory path
        
    Returns:
        Global DataLoader instance
    """
    global _global_loader
    if _global_loader is None:
        _global_loader = DataLoader(data_dir)
    return _global_loader


def reset_global_loader() -> None:
    """Reset global loader (useful for testing)."""
    global _global_loader
    _global_loader = None

