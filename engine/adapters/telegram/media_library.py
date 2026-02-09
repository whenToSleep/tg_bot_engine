"""Media Library - Cache Telegram file IDs to avoid re-uploading files.

This module provides file caching for Telegram media (images, documents, etc.)
to improve performance and reduce traffic.

When sending a local file for the first time, Telegram returns a file_id.
This file_id can be reused instead of uploading the file again.

Example:
    >>> from engine.adapters.telegram.media_library import MediaLibrary
    >>> 
    >>> library = MediaLibrary()
    >>> 
    >>> # First time: Upload file
    >>> local_path = "cards/dragon.png"
    >>> file_id = library.get_or_cache(local_path, None)
    >>> # file_id is None, need to upload
    >>> 
    >>> # After upload, save file_id
    >>> library.save_file_id(local_path, "AgACAgIAAxkBAAI...")
    >>> 
    >>> # Next time: Use cached file_id
    >>> file_id = library.get_or_cache(local_path, None)
    >>> # file_id = "AgACAgIAAxkBAAI..." (cached)
"""

from typing import Dict, Any, Optional
import json
import os
from pathlib import Path


class MediaLibrary:
    """Cache for Telegram file IDs.
    
    Maintains a mapping of local_path -> file_id to avoid
    re-uploading media files.
    
    Cache can be persisted to disk for reuse across bot restarts.
    
    Example:
        >>> library = MediaLibrary(cache_file="media_cache.json")
        >>> 
        >>> # Check cache
        >>> file_id = library.get_file_id("images/card_1.png")
        >>> if file_id:
        ...     # Use cached file_id
        ...     await message.answer_photo(file_id)
        ... else:
        ...     # Upload file and cache result
        ...     msg = await message.answer_photo(FSInputFile("images/card_1.png"))
        ...     library.save_file_id("images/card_1.png", msg.photo[-1].file_id)
    """
    
    def __init__(self, cache_file: Optional[str] = None):
        """Initialize media library.
        
        Args:
            cache_file: Optional path to cache file (JSON)
        """
        self.cache_file = cache_file
        self.cache: Dict[str, str] = {}
        
        # Load cache from file if exists
        if cache_file and os.path.exists(cache_file):
            self.load_from_file()
    
    def get_file_id(self, local_path: str) -> Optional[str]:
        """Get cached file ID for a local path.
        
        Args:
            local_path: Path to local file
            
        Returns:
            Cached file_id or None if not cached
            
        Example:
            >>> library = MediaLibrary()
            >>> library.save_file_id("test.png", "file_123")
            >>> library.get_file_id("test.png")
            'file_123'
            >>> library.get_file_id("nonexistent.png")
            None
        """
        # Normalize path
        normalized = str(Path(local_path).as_posix())
        return self.cache.get(normalized)
    
    def save_file_id(self, local_path: str, file_id: str) -> None:
        """Save file ID for a local path.
        
        Args:
            local_path: Path to local file
            file_id: Telegram file_id
            
        Example:
            >>> library = MediaLibrary()
            >>> library.save_file_id("cards/dragon.png", "AgACAgIAAxkBAAI...")
            >>> library.get_file_id("cards/dragon.png")
            'AgACAgIAAxkBAAI...'
        """
        # Normalize path
        normalized = str(Path(local_path).as_posix())
        self.cache[normalized] = file_id
        
        # Auto-save to file if configured
        if self.cache_file:
            self.save_to_file()
    
    def has_file(self, local_path: str) -> bool:
        """Check if file is cached.
        
        Args:
            local_path: Path to local file
            
        Returns:
            True if file_id is cached
            
        Example:
            >>> library = MediaLibrary()
            >>> library.save_file_id("test.png", "file_123")
            >>> library.has_file("test.png")
            True
        """
        return self.get_file_id(local_path) is not None
    
    def remove_file(self, local_path: str) -> bool:
        """Remove file from cache.
        
        Args:
            local_path: Path to local file
            
        Returns:
            True if file was removed, False if not in cache
            
        Example:
            >>> library = MediaLibrary()
            >>> library.save_file_id("test.png", "file_123")
            >>> library.remove_file("test.png")
            True
            >>> library.remove_file("test.png")
            False
        """
        normalized = str(Path(local_path).as_posix())
        if normalized in self.cache:
            del self.cache[normalized]
            
            if self.cache_file:
                self.save_to_file()
            
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cached file IDs.
        
        Example:
            >>> library = MediaLibrary()
            >>> library.save_file_id("test.png", "file_123")
            >>> library.clear()
            >>> library.get_file_id("test.png")
            None
        """
        self.cache.clear()
        
        if self.cache_file:
            self.save_to_file()
    
    def get_cache_size(self) -> int:
        """Get number of cached files.
        
        Returns:
            Number of files in cache
            
        Example:
            >>> library = MediaLibrary()
            >>> library.save_file_id("file1.png", "id1")
            >>> library.save_file_id("file2.png", "id2")
            >>> library.get_cache_size()
            2
        """
        return len(self.cache)
    
    def get_all_paths(self) -> list[str]:
        """Get all cached file paths.
        
        Returns:
            List of local paths
            
        Example:
            >>> library = MediaLibrary()
            >>> library.save_file_id("file1.png", "id1")
            >>> library.save_file_id("file2.png", "id2")
            >>> paths = library.get_all_paths()
            >>> len(paths)
            2
        """
        return list(self.cache.keys())
    
    def save_to_file(self) -> None:
        """Save cache to file.
        
        Example:
            >>> library = MediaLibrary(cache_file="test_cache.json")
            >>> library.save_file_id("test.png", "file_123")
            >>> # Cache automatically saved to test_cache.json
        """
        if not self.cache_file:
            return
        
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to save media cache: {e}")
    
    def load_from_file(self) -> None:
        """Load cache from file.
        
        Example:
            >>> library = MediaLibrary(cache_file="test_cache.json")
            >>> # Cache automatically loaded from file
        """
        if not self.cache_file or not os.path.exists(self.cache_file):
            return
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                self.cache = json.load(f)
        except Exception as e:
            print(f"Failed to load media cache: {e}")
            self.cache = {}
    
    def get_or_cache(
        self,
        local_path: str,
        file_id_from_upload: Optional[str]
    ) -> Optional[str]:
        """Get cached file_id or cache new one.
        
        Convenience method for: check cache -> upload if needed -> cache result.
        
        Args:
            local_path: Path to local file
            file_id_from_upload: file_id after upload (None if not uploaded yet)
            
        Returns:
            Cached file_id or None if needs upload
            
        Example:
            >>> library = MediaLibrary()
            >>> 
            >>> # First call: no cache
            >>> result = library.get_or_cache("test.png", None)
            >>> result is None  # Need to upload
            True
            >>> 
            >>> # After upload, cache it
            >>> result = library.get_or_cache("test.png", "file_123")
            >>> result  # Now cached
            'file_123'
            >>> 
            >>> # Next call: from cache
            >>> result = library.get_or_cache("test.png", None)
            >>> result
            'file_123'
        """
        # Check cache first
        cached = self.get_file_id(local_path)
        if cached:
            return cached
        
        # If file_id provided, cache it
        if file_id_from_upload:
            self.save_file_id(local_path, file_id_from_upload)
            return file_id_from_upload
        
        # No cache, no upload -> return None
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Export cache as dictionary.
        
        Returns:
            Dictionary representation
            
        Example:
            >>> library = MediaLibrary()
            >>> library.save_file_id("test.png", "file_123")
            >>> data = library.to_dict()
            >>> data["cache"]
            {'test.png': 'file_123'}
        """
        return {
            "cache_file": self.cache_file,
            "cache": self.cache,
            "size": len(self.cache)
        }


# Global media library instance
_global_media_library: Optional[MediaLibrary] = None


def get_media_library(cache_file: str = "media_cache.json") -> MediaLibrary:
    """Get global media library instance.
    
    Args:
        cache_file: Path to cache file
        
    Returns:
        Global MediaLibrary instance
        
    Example:
        >>> library = get_media_library()
        >>> library.save_file_id("test.png", "file_123")
        >>> 
        >>> # In another module
        >>> library2 = get_media_library()
        >>> library2.get_file_id("test.png")
        'file_123'
    """
    global _global_media_library
    
    if _global_media_library is None:
        _global_media_library = MediaLibrary(cache_file)
    
    return _global_media_library


def reset_media_library() -> None:
    """Reset global media library.
    
    Useful for testing or reinitialization.
    
    Example:
        >>> library = get_media_library()
        >>> library.save_file_id("test.png", "file_123")
        >>> 
        >>> reset_media_library()
        >>> 
        >>> library2 = get_media_library()
        >>> library2.get_file_id("test.png")  # Cache cleared
        None
    """
    global _global_media_library
    _global_media_library = None

