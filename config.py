"""
Core configuration for LLM Auction Optimization experiments.
"""

from dataclasses import dataclass
from typing import Literal


@dataclass
class ExperimentConfig:
    """Configuration for a single experiment run."""
    
    # Task
    task_type: Literal["diagnosis", "triage", "treatment", "risk_assessment"] = "diagnosis"
    
    # Baseline
    baseline: Literal["free_discussion", "turn_taking", "auction"] = "auction"
    
    # Budget & Pricing
    initial_budget: float = 1.0
    token_price: float = 0.001  # Cost per token
    
    # Auction type
    auction_type: Literal["sealed_bid", "vickrey", "all_pay"] = "sealed_bid"
    
    # Reward
    reward_amount: float = 1.0
    safety_bonus: float = 0.25
    
    # Constraints
    max_tokens_per_message: int = 60
    n_agents: int = 20
    
    # Communication style
    communication_styles: list[str] = None  # e.g., ["assertive", "timid", "calibrated"]
    
    def __post_init__(self):
        if self.communication_styles is None:
            self.communication_styles = ["neutral"] * self.n_agents


# Default experiment configurations for hackathon

# Baseline A: Free Discussion
FREE_DISCUSSION = ExperimentConfig(
    baseline="free_discussion",
    task_type="diagnosis"
)

# Baseline B: Turn-Taking
TURN_TAKING = ExperimentConfig(
    baseline="turn_taking",
    task_type="diagnosis"
)

# Main Method: Auction
AUCTION_SEALED_BID = ExperimentConfig(
    baseline="auction",
    task_type="diagnosis",
    auction_type="sealed_bid",
    token_price=0.001
)

# Auction with Vickrey (Second-Price)
AUCTION_VICKREY = ExperimentConfig(
    baseline="auction",
    task_type="diagnosis",
    auction_type="vickrey",
    token_price=0.001
)

# Token price sweep configs
AUCTION_LOW_PRICE = ExperimentConfig(
    baseline="auction",
    task_type="diagnosis",
    auction_type="sealed_bid",
    token_price=0.0005
)

AUCTION_HIGH_PRICE = ExperimentConfig(
    baseline="auction",
    task_type="diagnosis",
    auction_type="sealed_bid",
    token_price=0.005
)

# Budget sweep configs
AUCTION_TIGHT_BUDGET = ExperimentConfig(
    baseline="auction",
    task_type="diagnosis",
    auction_type="sealed_bid",
    initial_budget=0.50,
    token_price=0.001
)

AUCTION_LOOSE_BUDGET = ExperimentConfig(
    baseline="auction",
    task_type="diagnosis",
    auction_type="sealed_bid",
    initial_budget=2.00,
    token_price=0.001
)

# Communication style variants
AUCTION_WITH_STYLES = ExperimentConfig(
    baseline="auction",
    task_type="diagnosis",
    auction_type="sealed_bid",
    token_price=0.001,
    communication_styles=["assertive", "timid", "calibrated", "cooperative", "competitive"]
)
