"""
LLM Auction Optimization Package

A system for studying how budgeted communication and auction mechanisms
affect multi-agent clinical decision-making.
"""

__version__ = "0.1.0"
__author__ = "Srivastava Lab Hackathon Team"

from .config import ExperimentConfig
from .data_types import (
    ClinicalVignette,
    PrivateAssessment,
    AuctionResult,
    Intervention,
    RoundOutcome,
    AgentState,
)
from .agents import Agent, MockAgent, LocalLLMAgent
from .auctions import run_auction, AuctionType
from .utils import ExperimentLogger, ExperimentMetrics, MetricsDisplay

__all__ = [
    "ExperimentConfig",
    "ClinicalVignette",
    "PrivateAssessment",
    "AuctionResult",
    "Intervention",
    "RoundOutcome",
    "AgentState",
    "Agent",
    "MockAgent",
    "LocalLLMAgent",
    "run_auction",
    "AuctionType",
    "ExperimentLogger",
    "ExperimentMetrics",
    "MetricsDisplay",
]
