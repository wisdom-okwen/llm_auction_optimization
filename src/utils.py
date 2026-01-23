"""
Utilities for logging, metrics, and analysis.
"""

import json
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path

from types import RoundOutcome, AgentState


class ExperimentLogger:
    """Log experiment results to file."""
    
    def __init__(self, output_dir: str = "./results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.log_entries = []
    
    def log_round(self, outcome: RoundOutcome) -> None:
        """Log a single round."""
        self.log_entries.append(outcome.summary())
    
    def save(self, filename: str = None) -> str:
        """Save logs to JSON."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"experiment_{timestamp}.json"
        
        filepath = self.output_dir / filename
        with open(filepath, 'w') as f:
            json.dump(self.log_entries, f, indent=2)
        
        print(f"Logged {len(self.log_entries)} rounds to {filepath}")
        return str(filepath)


class ExperimentMetrics:
    """Compute metrics from round outcomes."""
    
    @staticmethod
    def compute_metrics(outcomes: List[RoundOutcome]) -> Dict[str, Any]:
        """
        Compute aggregate metrics.
        
        Args:
            outcomes: List of RoundOutcome objects
        
        Returns:
            Dict with metrics: accuracy, cost, efficiency, etc.
        """
        if not outcomes:
            return {}
        
        correctness = sum(1 for o in outcomes if o.correctness) / len(outcomes)
        avg_cost = sum(o.total_cost for o in outcomes) / len(outcomes)
        avg_tokens = sum(o.total_tokens for o in outcomes) / len(outcomes)
        
        # Proposer accuracy
        proposer_correct = sum(
            1 for o in outcomes
            if o.private_assessments[o.auction_result.proposer_id].recommended_action == o.ground_truth_action
        ) / len(outcomes)
        
        # Intervention impact
        intervention_rounds = [o for o in outcomes if o.interventions]
        intervention_success_rate = 0.0
        if intervention_rounds:
            intervention_success_rate = sum(
                1 for o in intervention_rounds
                if any(i.suggested_alternative_action == o.ground_truth_action for i in o.interventions if i.suggested_alternative_action)
            ) / len(intervention_rounds)
        
        # Efficiency
        efficiency = correctness / avg_cost if avg_cost > 0 else 0.0
        
        return {
            'n_rounds': len(outcomes),
            'accuracy': correctness,
            'avg_cost_per_round': avg_cost,
            'avg_tokens_per_round': avg_tokens,
            'efficiency': efficiency,
            'proposer_accuracy': proposer_correct,
            'avg_interventions': sum(len(o.interventions) for o in outcomes) / len(outcomes),
            'intervention_success_rate': intervention_success_rate,
        }
    
    @staticmethod
    def compute_agent_stats(agent_states: Dict[str, AgentState]) -> Dict[str, Any]:
        """Compute per-agent statistics."""
        stats = {}
        for agent_id, state in agent_states.items():
            stats[agent_id] = {
                'communication_style': state.communication_style,
                'rounds_participated': state.rounds_participated,
                'times_proposer': state.times_proposer,
                'proposer_accuracy_rate': (
                    state.times_proposer_correct / state.times_proposer
                    if state.times_proposer > 0 else 0.0
                ),
                'interventions_made': state.interventions_made,
                'interventions_valuable_rate': (
                    state.interventions_valuable / state.interventions_made
                    if state.interventions_made > 0 else 0.0
                ),
                'total_tokens_used': state.total_tokens_used,
                'total_bids_paid': state.total_bids_paid,
                'cumulative_reward': state.cumulative_reward,
                'efficiency': state.efficiency(),
            }
        return stats


class MetricsDisplay:
    """Pretty-print metrics."""
    
    @staticmethod
    def print_summary(metrics: Dict[str, Any]) -> None:
        """Print experiment summary."""
        print("\n" + "=" * 60)
        print("EXPERIMENT SUMMARY")
        print("=" * 60)
        print(f"Rounds:                  {metrics.get('n_rounds', 'N/A')}")
        print(f"Accuracy:                {metrics.get('accuracy', 0):.1%}")
        print(f"Avg Cost per Round:      ${metrics.get('avg_cost_per_round', 0):.4f}")
        print(f"Avg Tokens per Round:    {metrics.get('avg_tokens_per_round', 0):.0f}")
        print(f"Efficiency (acc/cost):   {metrics.get('efficiency', 0):.2f}")
        print(f"Proposer Accuracy:       {metrics.get('proposer_accuracy', 0):.1%}")
        print(f"Avg Interventions:       {metrics.get('avg_interventions', 0):.2f}")
        print(f"Intervention Success:    {metrics.get('intervention_success_rate', 0):.1%}")
        print("=" * 60 + "\n")
    
    @staticmethod
    def print_agent_stats(agent_stats: Dict[str, Any]) -> None:
        """Print per-agent statistics."""
        print("\n" + "=" * 60)
        print("PER-AGENT STATISTICS")
        print("=" * 60)
        for agent_id, stats in agent_stats.items():
            print(f"\n{agent_id} ({stats['communication_style']})")
            print(f"  Rounds participated:   {stats['rounds_participated']}")
            print(f"  Times proposer:        {stats['times_proposer']}")
            print(f"  Proposer accuracy:     {stats['proposer_accuracy_rate']:.1%}")
            print(f"  Interventions made:    {stats['interventions_made']}")
            print(f"  Interventions valuable: {stats['interventions_valuable_rate']:.1%}")
            print(f"  Tokens used:           {stats['total_tokens_used']}")
            print(f"  Bids paid:             ${stats['total_bids_paid']:.4f}")
            print(f"  Net reward:            ${stats['cumulative_reward']:.4f}")
            print(f"  Efficiency:            {stats['efficiency']:.2f}")
        print("=" * 60 + "\n")
