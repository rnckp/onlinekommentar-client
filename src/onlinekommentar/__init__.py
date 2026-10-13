"""Independent Python client for the public Onlinekommentar APIs."""

from .client import OnlinekommentarClient, PaginationLimitError
from .config import DEFAULT_CONFIG, OnlinekommentarConfig, load_config
from .models import Commentary, CommentarySearchResult, LegislativeAct, Person
from .oai import OAIProtocolError, parse_oai_response

__version__ = "0.1.0"

__all__ = [
    "Commentary",
    "CommentarySearchResult",
    "DEFAULT_CONFIG",
    "LegislativeAct",
    "OnlinekommentarClient",
    "OnlinekommentarConfig",
    "OAIProtocolError",
    "PaginationLimitError",
    "Person",
    "load_config",
    "parse_oai_response",
]
