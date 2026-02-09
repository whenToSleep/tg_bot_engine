"""Matchmaking Service - PvP opponent matching and ranking system.

This module provides matchmaking and ranking for PvP games:
- ELO-based rating system
- Opponent matching by rating range
- Seasonal rankings
- Leaderboards

Designed for async PvP (e.g., "Arena of Shadows" in Aether Bonds).

Example:
    >>> from engine.services.matchmaking import MatchmakingService
    >>> 
    >>> service = MatchmakingService()
    >>> player = {"_id": "p1", "rating": 1500}
    >>> 
    >>> # Find opponent
    >>> all_players = state.get_entities_by_type("player")
    >>> opponent = service.find_opponent(player, all_players)
    >>> 
    >>> # After match
    >>> service.update_ratings_after_match(player, opponent, player_won=True)
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import random


@dataclass
class MatchResult:
    """Result of a PvP match.
    
    Attributes:
        winner_id: ID of winning player
        loser_id: ID of losing player
        winner_rating_change: Rating change for winner
        loser_rating_change: Rating change for loser
        new_winner_rating: Winner's new rating
        new_loser_rating: Loser's new rating
    """
    winner_id: str
    loser_id: str
    winner_rating_change: int
    loser_rating_change: int
    new_winner_rating: int
    new_loser_rating: int


class RankingSystem:
    """ELO-based ranking system.
    
    Provides rating calculation and rank tier assignment.
    
    Example:
        >>> ranking = RankingSystem()
        >>> player_rating = 1500
        >>> opponent_rating = 1600
        >>> delta = ranking.calculate_rating_change(player_rating, opponent_rating, won=True)
        >>> new_rating = player_rating + delta
    """
    
    # Rank tiers based on rating
    RANK_TIERS = [
        (0, "Bronze"),
        (1200, "Silver"),
        (1500, "Gold"),
        (1800, "Platinum"),
        (2100, "Diamond"),
        (2500, "Master"),
        (3000, "Grandmaster")
    ]
    
    def __init__(self, k_factor: int = 32, initial_rating: int = 1200):
        """Initialize ranking system.
        
        Args:
            k_factor: ELO K-factor (higher = more volatile changes)
            initial_rating: Starting rating for new players
        """
        self.k_factor = k_factor
        self.initial_rating = initial_rating
    
    def calculate_expected_score(
        self,
        player_rating: int,
        opponent_rating: int
    ) -> float:
        """Calculate expected win probability (0.0 - 1.0).
        
        Uses ELO formula: 1 / (1 + 10^((opponent - player) / 400))
        
        Args:
            player_rating: Player's rating
            opponent_rating: Opponent's rating
            
        Returns:
            Expected score (0.0 = certain loss, 1.0 = certain win)
            
        Example:
            >>> ranking = RankingSystem()
            >>> ranking.calculate_expected_score(1500, 1500)
            0.5
            >>> ranking.calculate_expected_score(1500, 1600)  # Underdog
            0.36
        """
        return 1 / (1 + 10 ** ((opponent_rating - player_rating) / 400))
    
    def calculate_rating_change(
        self,
        player_rating: int,
        opponent_rating: int,
        won: bool
    ) -> int:
        """Calculate rating change after a match.
        
        Args:
            player_rating: Player's current rating
            opponent_rating: Opponent's rating
            won: Whether player won
            
        Returns:
            Rating change (positive or negative)
            
        Example:
            >>> ranking = RankingSystem()
            >>> # Win against equal opponent
            >>> ranking.calculate_rating_change(1500, 1500, won=True)
            16
            >>> # Lose against equal opponent
            >>> ranking.calculate_rating_change(1500, 1500, won=False)
            -16
            >>> # Win against stronger opponent (upset)
            >>> ranking.calculate_rating_change(1500, 1600, won=True)
            20
        """
        expected = self.calculate_expected_score(player_rating, opponent_rating)
        actual = 1.0 if won else 0.0
        
        return int(self.k_factor * (actual - expected))
    
    def get_rank_tier(self, rating: int) -> str:
        """Get rank tier name based on rating.
        
        Args:
            rating: Player rating
            
        Returns:
            Rank tier name
            
        Example:
            >>> ranking = RankingSystem()
            >>> ranking.get_rank_tier(1000)
            'Bronze'
            >>> ranking.get_rank_tier(1600)
            'Gold'
            >>> ranking.get_rank_tier(2200)
            'Diamond'
        """
        for min_rating, tier in reversed(self.RANK_TIERS):
            if rating >= min_rating:
                return tier
        return "Unranked"
    
    def initialize_player_rating(self, player: Dict[str, Any]) -> None:
        """Initialize rating fields for a new player.
        
        Args:
            player: Player entity
            
        Example:
            >>> player = {"_id": "player_1"}
            >>> ranking = RankingSystem()
            >>> ranking.initialize_player_rating(player)
            >>> player["rating"]
            1200
            >>> player["rank_tier"]
            'Silver'
        """
        if "rating" not in player:
            player["rating"] = self.initial_rating
        
        if "rank_tier" not in player:
            player["rank_tier"] = self.get_rank_tier(player["rating"])
        
        if "wins" not in player:
            player["wins"] = 0
        
        if "losses" not in player:
            player["losses"] = 0


class MatchmakingService:
    """Service for finding PvP opponents and managing rankings.
    
    Features:
    - Find opponents within rating range
    - Update ratings after matches
    - Generate leaderboards
    - Track win/loss records
    
    Example:
        >>> service = MatchmakingService()
        >>> player = {"_id": "p1", "rating": 1500}
        >>> 
        >>> # Initialize if needed
        >>> service.ranking.initialize_player_rating(player)
        >>> 
        >>> # Find opponent
        >>> opponents = [{"_id": "p2", "rating": 1480}, {"_id": "p3", "rating": 1520}]
        >>> opponent = service.find_opponent(player, opponents)
    """
    
    def __init__(
        self,
        ranking_system: Optional[RankingSystem] = None,
        max_rating_diff: int = 200
    ):
        """Initialize matchmaking service.
        
        Args:
            ranking_system: Optional custom ranking system
            max_rating_diff: Maximum rating difference for matchmaking
        """
        self.ranking = ranking_system or RankingSystem()
        self.max_rating_diff = max_rating_diff
    
    def find_opponent(
        self,
        player: Dict[str, Any],
        available_players: List[Dict[str, Any]],
        exclude_ids: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Find a suitable opponent for the player.
        
        Matching criteria:
        1. Not the player themselves
        2. Not in exclude_ids
        3. Within rating range (max_rating_diff)
        4. Closest rating preferred
        
        Args:
            player: Player looking for match
            available_players: Pool of potential opponents
            exclude_ids: Optional list of IDs to exclude
            
        Returns:
            Opponent entity or None if no suitable match
            
        Example:
            >>> service = MatchmakingService(max_rating_diff=100)
            >>> player = {"_id": "p1", "rating": 1500}
            >>> pool = [
            ...     {"_id": "p2", "rating": 1550},  # Within range
            ...     {"_id": "p3", "rating": 1700},  # Out of range
            ... ]
            >>> opponent = service.find_opponent(player, pool)
            >>> opponent["_id"]
            'p2'
        """
        player_id = player.get("_id")
        player_rating = player.get("rating", self.ranking.initial_rating)
        exclude_ids = exclude_ids or []
        
        # Filter candidates
        candidates = []
        for candidate in available_players:
            candidate_id = candidate.get("_id")
            candidate_rating = candidate.get("rating", self.ranking.initial_rating)
            
            # Skip self and excluded
            if candidate_id == player_id or candidate_id in exclude_ids:
                continue
            
            # Check rating range
            rating_diff = abs(candidate_rating - player_rating)
            if rating_diff <= self.max_rating_diff:
                candidates.append((candidate, rating_diff))
        
        if not candidates:
            return None
        
        # Sort by rating difference (prefer closest)
        candidates.sort(key=lambda x: x[1])
        
        # Return closest match (or random from top 3 if available)
        top_candidates = candidates[:min(3, len(candidates))]
        return random.choice(top_candidates)[0]
    
    def update_ratings_after_match(
        self,
        winner: Dict[str, Any],
        loser: Dict[str, Any]
    ) -> MatchResult:
        """Update player ratings after a match.
        
        Args:
            winner: Winning player entity
            loser: Losing player entity
            
        Returns:
            MatchResult with rating changes
            
        Example:
            >>> service = MatchmakingService()
            >>> winner = {"_id": "p1", "rating": 1500, "wins": 10}
            >>> loser = {"_id": "p2", "rating": 1600, "losses": 5}
            >>> 
            >>> result = service.update_ratings_after_match(winner, loser)
            >>> winner["rating"]  # Increased (upset win)
            1520
            >>> loser["rating"]  # Decreased
            1580
        """
        # Get current ratings
        winner_rating = winner.get("rating", self.ranking.initial_rating)
        loser_rating = loser.get("rating", self.ranking.initial_rating)
        
        # Calculate changes
        winner_change = self.ranking.calculate_rating_change(
            winner_rating, loser_rating, won=True
        )
        loser_change = self.ranking.calculate_rating_change(
            loser_rating, winner_rating, won=False
        )
        
        # Update ratings
        winner["rating"] = winner_rating + winner_change
        loser["rating"] = loser_rating + loser_change
        
        # Update rank tiers
        winner["rank_tier"] = self.ranking.get_rank_tier(winner["rating"])
        loser["rank_tier"] = self.ranking.get_rank_tier(loser["rating"])
        
        # Update win/loss counts
        winner["wins"] = winner.get("wins", 0) + 1
        loser["losses"] = loser.get("losses", 0) + 1
        
        return MatchResult(
            winner_id=winner["_id"],
            loser_id=loser["_id"],
            winner_rating_change=winner_change,
            loser_rating_change=loser_change,
            new_winner_rating=winner["rating"],
            new_loser_rating=loser["rating"]
        )
    
    def generate_leaderboard(
        self,
        players: List[Dict[str, Any]],
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Generate leaderboard sorted by rating.
        
        Args:
            players: List of player entities
            limit: Maximum number of entries
            
        Returns:
            Sorted list of players with rank positions
            
        Example:
            >>> players = [
            ...     {"_id": "p1", "rating": 1600},
            ...     {"_id": "p2", "rating": 1800},
            ...     {"_id": "p3", "rating": 1500}
            ... ]
            >>> leaderboard = service.generate_leaderboard(players)
            >>> leaderboard[0]["rank_position"]
            1
            >>> leaderboard[0]["_id"]
            'p2'
        """
        # Sort by rating (descending)
        sorted_players = sorted(
            players,
            key=lambda p: p.get("rating", 0),
            reverse=True
        )[:limit]
        
        # Add rank positions
        for idx, player in enumerate(sorted_players):
            player["rank_position"] = idx + 1
        
        return sorted_players
    
    def get_player_rank(
        self,
        player: Dict[str, Any],
        all_players: List[Dict[str, Any]]
    ) -> int:
        """Get player's rank position among all players.
        
        Args:
            player: Player to check
            all_players: All players in ranking
            
        Returns:
            Rank position (1 = best)
            
        Example:
            >>> player = {"_id": "p1", "rating": 1500}
            >>> all_players = [player, {"_id": "p2", "rating": 1600}]
            >>> service.get_player_rank(player, all_players)
            2
        """
        player_rating = player.get("rating", 0)
        
        # Count players with higher rating
        rank = 1
        for other in all_players:
            if other.get("_id") != player.get("_id"):
                if other.get("rating", 0) > player_rating:
                    rank += 1
        
        return rank

