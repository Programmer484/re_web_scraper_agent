"""PropertySearch-Agent package

This package provides a clean interface for property search functionality
that can be easily integrated into web applications.
"""

from .models import Listing, SearchFilters
from .run_agent import main


# Export the main interface and models
__all__ = ["run_agent", "Listing", "SearchFilters"] 