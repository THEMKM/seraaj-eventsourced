"""Matching Service

Implements volunteer-opportunity matching using a sophisticated scoring algorithm
that considers distance, skills, and availability.
"""
from .api import app
from .service import MatchingService
from .algorithm import MatchingAlgorithm

__all__ = ["app", "MatchingService", "MatchingAlgorithm"]