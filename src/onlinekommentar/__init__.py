"""Independent Python client for the public Onlinekommentar APIs."""

from .client import OnlinekommentarClient
from .config import DEFAULT_CONFIG, OnlinekommentarConfig, load_config
from .models import Commentary, CommentarySearchResult, LegislativeAct, Person

__version__ = "0.1.0"

__all__ = [
    "Commentary",
    "CommentarySearchResult",
    "DEFAULT_CONFIG",
    "LegislativeAct",
    "OnlinekommentarClient",
    "OnlinekommentarConfig",
    "Person",
    "load_config",
]
