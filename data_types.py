"""
Core data structures and types for the auction system.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from datetime import datetime


@dataclass
class ClinicalVignette:
    """A single clinical case vignette."""
    
    vignette_id: str
    text: str
    ground_truth_action: str
    options: List[str]  # e.g., ["Diagnosis A", "Diagnosis B", ...]
    task_type: str  # "diagnosis", "triage", "treatment", "risk_assessment"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PrivateAssessment:
    """Agent's private assessment before auction."""
    
    agent_id: str
    recommended_action: str
    confidence: float  # [0, 1]
    rationale: str  # 1-3 bullet points


@dataclass
class AuctionResult:
    """Result of the proposer auction."""
    
    proposer_id: str
    proposer_bid: float
    all_bids: Dict[str, float]  # agent_id -> bid


@dataclass
class Intervention:
    """An agent's paid intervention message."""
    
    agent_id: str
    message: str
    token_count: int
    cost: float
    suggested_alternative_action: Optional[str] = None


@dataclass
class RoundOutcome:
    """Full outcome of one clinical auction round."""
    
    timestamp: datetime
    vignette: ClinicalVignette
    round_id: int
    
    # Round 0: Private Assessments
    private_assessments: Dict[str, PrivateAssessment]
    
    # Round 1: Auction
    auction_result: AuctionResult
    
    # Round 2: Interventions
    interventions: List[Intervention]
    
    # Round 3: Vote
    votes: Dict[str, str]  # agent_id -> voted_action
    
    # Round 4: Outcome
    final_action: str
    ground_truth_action: str
    correctness: bool
    
    # Costs and rewards
    total_tokens: int
    total_cost: float
    agent_rewards: Dict[str, float]  # agent_id -> net reward
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def summary(self) -> Dict[str, Any]:
        """Return a summary dict for logging/analysis."""
        return {
            'vignette_id': self.vignette.vignette_id,
            'proposer_id': self.auction_result.proposer_id,
            'proposer_bid': self.auction_result.proposer_bid,
            'intervention_count': len(self.interventions),
            'final_action': self.final_action,
            'ground_truth': self.ground_truth_action,
            'correctness': self.correctness,
            'total_tokens': self.total_tokens,
            'total_cost': self.total_cost,
            'avg_agent_reward': sum(self.agent_rewards.values()) / len(self.agent_rewards) if self.agent_rewards else 0
        }


@dataclass
class AgentState:
    """State of an agent across multiple rounds."""
    
    agent_id: str
    initial_budget: float
    remaining_budget: float
    communication_style: str = "neutral"
    
    # Cumulative stats
    rounds_participated: int = 0
    times_proposer: int = 0
    times_proposer_correct: int = 0
    interventions_made: int = 0
    interventions_valuable: int = 0  # Changed outcome to correct
    total_tokens_used: int = 0
    total_bids_paid: float = 0.0
    cumulative_reward: float = 0.0
    
    def efficiency(self) -> float:
        """Correctness per dollar spent."""
        if self.total_bids_paid + self.total_tokens_used * 0.001 > 0:
            return self.cumulative_reward / (self.total_bids_paid + self.total_tokens_used * 0.001)
        return 0.0
