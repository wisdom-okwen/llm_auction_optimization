"""
Data logging utilities for simulation results.
Saves experiment data to CSVs for analysis.
"""

import os
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from collections import defaultdict
import pandas as pd


class SimulationLogger:
    """Logs simulation results to organized CSV files."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Create timestamp for this run
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_dir = self.data_dir / f"run_{self.timestamp}"
        self.run_dir.mkdir(exist_ok=True)
        
        # Initialize CSV files
        self.vignette_results_file = self.run_dir / "vignette_results.csv"
        self.agent_round_file = self.run_dir / "agent_round_results.csv"
        self.bid_data_file = self.run_dir / "bid_data.csv"
        self.agent_summary_file = self.run_dir / "agent_summary.csv"
        self.simulation_summary_file = self.run_dir / "simulation_summary.csv"
        
        # Write headers
        self._init_csv_headers()
        
        print(f"✓ Logging to: {self.run_dir}")
    
    def _init_csv_headers(self):
        """Initialize CSV files with headers."""
        
        # Vignette results
        with open(self.vignette_results_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'round_num', 'vignette_id', 'category', 'proposer_id', 
                'n_interventions', 'consensus_answer', 'consensus_votes',
                'correctness', 'total_cost', 'total_reward', 'n_agents'
            ])
            writer.writeheader()
        
        # Agent round results (one row per agent per round)
        with open(self.agent_round_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'round_num', 'vignette_id', 'agent_id', 'communication_style',
                'assessment_choice', 'assessment_confidence', 'bid_amount',
                'was_proposer', 'proposal_cost', 'intervention_cost',
                'final_vote', 'agent_reward', 'agent_total_cost',
                'budget_remaining'
            ])
            writer.writeheader()
        
        # Bid data (all bids per round)
        with open(self.bid_data_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'round_num', 'vignette_id', 'agent_id', 'communication_style',
                'confidence', 'bid_amount', 'winning_bid', 'winner'
            ])
            writer.writeheader()
        
        # Agent summary (aggregate per agent across all rounds)
        with open(self.agent_summary_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'agent_id', 'communication_style', 'total_rounds',
                'times_proposer', 'total_bids_made', 'avg_bid',
                'total_interventions', 'avg_intervention_cost',
                'total_cost', 'total_reward', 'net_benefit',
                'avg_reward_per_round', 'final_budget'
            ])
            writer.writeheader()
    
    def log_vignette_round(self, round_num: int, round_results: Dict[str, Any]):
        """Log results for one vignette round."""
        row = {
            'round_num': round_num,
            'vignette_id': round_results['vignette_id'],
            'category': round_results['vignette_category'],
            'proposer_id': round_results['proposer'],
            'n_interventions': len(round_results['interventions']),
            'consensus_answer': str(round_results['consensus_answer'])[:100],
            'consensus_votes': round_results['consensus_votes'],
            'correctness': round_results['correctness'],
            'total_cost': f"{round_results['total_costs']:.6f}",
            'total_reward': f"{round_results['total_rewards']:.6f}",
            'n_agents': len(round_results['agents'])
        }
        
        with open(self.vignette_results_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'round_num', 'vignette_id', 'category', 'proposer_id',
                'n_interventions', 'consensus_answer', 'consensus_votes',
                'correctness', 'total_cost', 'total_reward', 'n_agents'
            ])
            writer.writerow(row)
    
    def log_agent_results(self, round_num: int, round_results: Dict[str, Any], agents: List[Any]):
        """Log per-agent results for one round."""
        rows = []
        
        for agent_id, agent_data in round_results['agents'].items():
            agent_obj = next((a for a in agents if a.agent_id == agent_id), None)
            if not agent_obj:
                continue
            
            assessment = agent_data.get('assessment', {})
            proposal_cost = 0.0
            intervention_cost = 0.0
            
            if agent_id == round_results['proposer']:
                # Find proposal cost
                for key, val in round_results['costs_by_agent'].items():
                    if key == agent_id:
                        # Need to extract from full cost (bid + proposal + interventions)
                        proposal_cost = round_results['costs_by_agent'][agent_id]
                        break
            
            if agent_id in round_results['interventions']:
                intervention_data = round_results['interventions'][agent_id]
                intervention_cost = intervention_data.get('cost', 0.0)
            
            row = {
                'round_num': round_num,
                'vignette_id': round_results['vignette_id'],
                'agent_id': agent_id,
                'communication_style': agent_obj.communication_style,
                'assessment_choice': str(assessment.get('option_choice', ''))[:80],
                'assessment_confidence': f"{assessment.get('confidence', 0.0):.3f}",
                'bid_amount': f"{round_results['bids'].get(agent_id, 0.0):.6f}",
                'was_proposer': 1 if agent_id == round_results['proposer'] else 0,
                'proposal_cost': f"{proposal_cost:.6f}",
                'intervention_cost': f"{intervention_cost:.6f}",
                'final_vote': str(round_results['votes'].get(agent_id, ''))[:80],
                'agent_reward': f"{agent_data.get('reward', 0.0):.6f}",
                'agent_total_cost': f"{round_results['costs_by_agent'].get(agent_id, 0.0):.6f}",
                'budget_remaining': f"{agent_obj.budget:.6f}"
            }
            rows.append(row)
        
        with open(self.agent_round_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'round_num', 'vignette_id', 'agent_id', 'communication_style',
                'assessment_choice', 'assessment_confidence', 'bid_amount',
                'was_proposer', 'proposal_cost', 'intervention_cost',
                'final_vote', 'agent_reward', 'agent_total_cost', 'budget_remaining'
            ])
            writer.writerows(rows)
    
    def log_bids(self, round_num: int, round_results: Dict[str, Any], agents: List[Any]):
        """Log all bids from a round."""
        rows = []
        bids = round_results['bids']
        proposer_id = round_results['proposer']
        max_bid = max(bids.values()) if bids else 0
        
        for agent_id, bid_amount in bids.items():
            agent_obj = next((a for a in agents if a.agent_id == agent_id), None)
            if not agent_obj:
                continue
            
            assessment = round_results['agents'][agent_id].get('assessment', {})
            
            row = {
                'round_num': round_num,
                'vignette_id': round_results['vignette_id'],
                'agent_id': agent_id,
                'communication_style': agent_obj.communication_style,
                'confidence': f"{assessment.get('confidence', 0.0):.3f}",
                'bid_amount': f"{bid_amount:.6f}",
                'winning_bid': f"{max_bid:.6f}",
                'winner': 1 if agent_id == proposer_id else 0
            }
            rows.append(row)
        
        with open(self.bid_data_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'round_num', 'vignette_id', 'agent_id', 'communication_style',
                'confidence', 'bid_amount', 'winning_bid', 'winner'
            ])
            writer.writerows(rows)
    
    def log_agent_summary(self, all_round_results: List[Dict], agents: List[Any]):
        """Log aggregate statistics per agent."""
        agent_stats = defaultdict(lambda: {
            'total_rounds': 0,
            'times_proposer': 0,
            'total_bids': 0,
            'total_bid_amount': 0.0,
            'interventions': 0,
            'intervention_cost': 0.0,
            'total_cost': 0.0,
            'total_reward': 0.0
        })
        
        for round_result in all_round_results:
            for agent_id in round_result['agents'].keys():
                agent_stats[agent_id]['total_rounds'] += 1
                
                # Count as proposer
                if agent_id == round_result['proposer']:
                    agent_stats[agent_id]['times_proposer'] += 1
                
                # Bid info
                agent_stats[agent_id]['total_bids'] += 1
                agent_stats[agent_id]['total_bid_amount'] += round_result['bids'].get(agent_id, 0.0)
                
                # Intervention info
                if agent_id in round_result['interventions']:
                    agent_stats[agent_id]['interventions'] += 1
                    agent_stats[agent_id]['intervention_cost'] += round_result['interventions'][agent_id].get('cost', 0.0)
                
                # Costs and rewards
                agent_stats[agent_id]['total_cost'] += round_result['costs_by_agent'].get(agent_id, 0.0)
                agent_stats[agent_id]['total_reward'] += round_result['agents'][agent_id].get('reward', 0.0)
        
        rows = []
        for agent_obj in agents:
            stats = agent_stats[agent_obj.agent_id]
            
            avg_bid = stats['total_bid_amount'] / stats['total_bids'] if stats['total_bids'] > 0 else 0
            avg_intervention_cost = stats['intervention_cost'] / stats['interventions'] if stats['interventions'] > 0 else 0
            net_benefit = stats['total_reward'] - stats['total_cost']
            avg_reward = stats['total_reward'] / stats['total_rounds'] if stats['total_rounds'] > 0 else 0
            
            row = {
                'agent_id': agent_obj.agent_id,
                'communication_style': agent_obj.communication_style,
                'total_rounds': stats['total_rounds'],
                'times_proposer': stats['times_proposer'],
                'total_bids_made': stats['total_bids'],
                'avg_bid': f"{avg_bid:.6f}",
                'total_interventions': stats['interventions'],
                'avg_intervention_cost': f"{avg_intervention_cost:.6f}",
                'total_cost': f"{stats['total_cost']:.6f}",
                'total_reward': f"{stats['total_reward']:.6f}",
                'net_benefit': f"{net_benefit:.6f}",
                'avg_reward_per_round': f"{avg_reward:.6f}",
                'final_budget': f"{agent_obj.budget:.6f}"
            }
            rows.append(row)
        
        with open(self.agent_summary_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'agent_id', 'communication_style', 'total_rounds',
                'times_proposer', 'total_bids_made', 'avg_bid',
                'total_interventions', 'avg_intervention_cost',
                'total_cost', 'total_reward', 'net_benefit',
                'avg_reward_per_round', 'final_budget'
            ])
            writer.writerows(rows)
    
    def log_simulation_summary(self, all_round_results: List[Dict], agents: List[Any]):
        """Log overall simulation statistics."""
        total_correctness = sum(r['correctness'] for r in all_round_results) / len(all_round_results)
        total_costs = sum(r['total_costs'] for r in all_round_results)
        total_rewards = sum(r['total_rewards'] for r in all_round_results)
        efficiency = total_correctness / (total_costs + 0.0001) if total_costs > 0 else 0
        
        row = {
            'n_vignettes': len(all_round_results),
            'n_agents': len(agents),
            'avg_correctness': f"{total_correctness:.4f}",
            'total_costs': f"{total_costs:.6f}",
            'total_rewards': f"{total_rewards:.6f}",
            'net_rewards': f"{total_rewards - total_costs:.6f}",
            'efficiency': f"{efficiency:.4f}",
            'timestamp': self.timestamp
        }
        
        with open(self.simulation_summary_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'n_vignettes', 'n_agents', 'avg_correctness', 'total_costs',
                'total_rewards', 'net_rewards', 'efficiency', 'timestamp'
            ])
            writer.writeheader()
            writer.writerow(row)
    
    def print_summary(self, all_round_results: List[Dict]):
        """Print data logging summary."""
        print("\n" + "="*70)
        print("DATA LOGGING SUMMARY")
        print("="*70)
        print(f"✓ Results saved to: {self.run_dir}")
        print(f"\nFiles created:")
        print(f"  - vignette_results.csv    (one row per vignette)")
        print(f"  - agent_round_results.csv (one row per agent per round)")
        print(f"  - bid_data.csv            (all bids)")
        print(f"  - agent_summary.csv       (aggregate per agent)")
        print(f"  - simulation_summary.csv  (overall statistics)")
        print(f"\nTo analyze: pandas.read_csv('{self.run_dir}/vignette_results.csv')")
