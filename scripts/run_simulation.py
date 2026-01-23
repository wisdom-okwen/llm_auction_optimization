#!/usr/bin/env python
"""
Run the LLM Auction simulation directly from terminal.
No Jupyter required - just run: python run_simulation.py
"""

import os
import sys
import json
import random
from collections import Counter, defaultdict
import pandas as pd
import numpy as np
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent dir to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.agents import Agent, MockAgent
from src.config import AUCTION_SEALED_BID
from src.data_logger import SimulationLogger

# Check for OpenAI API key
# Set to False to use mock agents for testing, True for real OpenAI API
use_real_openai = os.environ.get('PERSONAL_OPENAI_KEY', '').startswith('sk-')

if use_real_openai:
    print("✓ Valid OpenAI API key detected - using real agents")
else:
    print("⚠️  Using MOCK agents (no real OpenAI calls)")
    print("To use real agents, set: export PERSONAL_OPENAI_KEY='sk-...'")
    print()

# Load the real dataset
print("\n" + "="*70)
print("STEP 1: Load Ethical Healthcare Vignettes")
print("="*70)

df_vignettes = pd.read_csv('datasets/Ethical-Reasoning-in-Mental-Health.csv')
print(f"✓ Loaded {len(df_vignettes)} ethical healthcare vignettes")

# Sample 5 vignettes 
n_vignettes = 5
sampled_indices = random.sample(range(len(df_vignettes)), n_vignettes)
sample_vignettes = df_vignettes.iloc[sampled_indices].to_dict('records')

print(f"✓ Selected {n_vignettes} vignettes for demo:")
for i, vig in enumerate(sample_vignettes, 1):
    print(f"  {i}. {vig['subcategory']}")

# Initialize 20 agents
print("\n" + "="*70)
print("STEP 2: Initialize 20 LLM Agents")
print("="*70)

n_agents = 20
styles = ['assertive'] * 5 + ['timid'] * 5 + ['calibrated'] * 5 + ['neutral'] * 5
random.shuffle(styles)

agents = []
for i in range(n_agents):
    agent_class = Agent if use_real_openai else MockAgent
    agent = agent_class(
        agent_id=f"agent_{i:02d}",
        communication_style=styles[i],
        budget=1.0
    )
    agents.append(agent)

agent_styles_count = Counter([a.communication_style for a in agents])
print(f"✓ Created {n_agents} agents:")
for style, count in agent_styles_count.items():
    print(f"  - {count:2d} {style:12s} agents")

print(f"Using: {'Real OpenAI API' if use_real_openai else 'Mock agents (no API calls)'}")

# Initialize data logger
logger = SimulationLogger(data_dir="data", mechanism="auction")

# Define auction mechanism
def run_sealed_bid_auction(bids):
    """Run a sealed-bid (first-price) auction."""
    if not bids:
        return None, 0
    winner_id = max(bids, key=bids.get)
    amount_paid = bids[winner_id]
    return winner_id, amount_paid

def run_auction_round(vignette, agents, config):
    """Run one complete auction round on a vignette."""
    vignette_id = vignette.get('id', 'unknown')
    round_results = {
        'vignette_id': vignette_id,
        'vignette_category': vignette.get('subcategory', ''),
        'agents': defaultdict(dict),
        'bids': {},
        'proposer': None,
        'proposal': None,
        'interventions': defaultdict(list),
        'votes': defaultdict(list),
        'costs_by_agent': defaultdict(float),
    }
    
    # PHASE 1: PRIVATE ASSESSMENT
    print(f"\n  Phase 1: Private Assessment")
    for agent in agents:
        assessment = agent.assess(vignette)
        round_results['agents'][agent.agent_id]['assessment'] = assessment
    print(f"    ✓ {len(agents)} agents assessed independently")
    
    # PHASE 2: SEALED-BID AUCTION
    print(f"  Phase 2: Sealed-Bid Auction")
    bids = {}
    for agent in agents:
        assessment = round_results['agents'][agent.agent_id]['assessment']
        bid = agent.bid(vignette, assessment)
        bids[agent.agent_id] = bid
    
    round_results['bids'] = bids
    proposer_id, auction_cost = run_sealed_bid_auction(bids)
    round_results['proposer'] = proposer_id
    round_results['costs_by_agent'][proposer_id] += auction_cost
    
    print(f"    ✓ Proposer: {proposer_id} (bid: ${auction_cost:.4f})")
    
    # PHASE 3: PROPOSAL & INTERVENTIONS
    print(f"  Phase 3: Proposal & Optional Critiques")
    proposer_agent = next(a for a in agents if a.agent_id == proposer_id)
    proposer_assessment = round_results['agents'][proposer_id]['assessment']
    proposal_result = proposer_agent.propose(vignette, proposer_assessment)
    round_results['proposal'] = proposal_result['proposal_text']
    round_results['costs_by_agent'][proposer_id] += proposal_result['cost']
    
    print(f"    ✓ Proposal: \"{proposal_result['proposal_text'][:80]}...\"")
    print(f"    ✓ Proposal cost: ${proposal_result['cost']:.4f}")
    
    # Non-proposers can intervene
    n_interventions = 0
    for agent in agents:
        if agent.agent_id != proposer_id:
            assessment = round_results['agents'][agent.agent_id]['assessment']
            intervention = agent.intervene(vignette, proposal_result['proposal_text'], assessment)
            if intervention:
                round_results['interventions'][agent.agent_id] = intervention
                round_results['costs_by_agent'][agent.agent_id] += intervention['cost']
                n_interventions += 1
    
    print(f"    ✓ Interventions: {n_interventions} agents critiqued the proposal")
    
    # PHASE 4: VOTING
    # PHASE 4: VOTING
    print(f"  Phase 4: Final Vote")
    options = vignette.get('options', [])
    if isinstance(options, str):
        try:
            options = json.loads(options)
        except:
            options = []
    
    votes = Counter()
    for agent in agents:
        # Get the agent's assessment from this round
        assessment = round_results['agents'][agent.agent_id].get('assessment', {})
        # Vote based on their assessment
        vote = assessment.get('option_choice', options[0] if options else "No consensus")
        votes[vote] += 1
        round_results['votes'][agent.agent_id] = vote
    
    consensus_answer = votes.most_common(1)[0][0] if votes else "No consensus"
    consensus_votes = votes[consensus_answer]
    round_results['consensus_answer'] = consensus_answer
    round_results['consensus_votes'] = consensus_votes
    
    # Check correctness
    expected_answer = vignette.get('expected_reasoning', '')
    correctness = 1.0 if consensus_answer and expected_answer in consensus_answer else 0.5
    round_results['correctness'] = correctness
    
    print(f"    ✓ Consensus: {consensus_votes}/{len(agents)} votes")
    print(f"    ✓ Correctness: {correctness:.0%}")
    
    # PHASE 5: PAYOFF
    print(f"  Phase 5: Payoff Calculation")
    reward_amount = 1.0 if correctness >= 0.8 else 0.5 if correctness >= 0.5 else 0.0
    round_results['reward_pool'] = reward_amount * len(agents)
    
    total_costs = sum(round_results['costs_by_agent'].values())
    total_rewards = 0.0
    
    for agent in agents:
        agent_cost = round_results['costs_by_agent'][agent.agent_id]
        agent_reward = reward_amount - agent_cost
        round_results['agents'][agent.agent_id]['reward'] = agent_reward
        total_rewards += agent_reward
    
    round_results['total_costs'] = total_costs
    round_results['total_rewards'] = total_rewards
    
    print(f"    ✓ Reward per agent: ${reward_amount:.4f}")
    print(f"    ✓ Total costs: ${total_costs:.4f}")
    print(f"    ✓ Total rewards: ${total_rewards:.4f}")
    
    return round_results

# Run simulation
print("\n" + "="*70)
print("STEP 3: Run Auction Simulation")
print("="*70)

all_round_results = []

for round_num, vignette in enumerate(sample_vignettes, 1):
    print(f"\nRound {round_num}: {vignette['subcategory']}")
    print("-" * 70)
    
    round_result = run_auction_round(vignette, agents, AUCTION_SEALED_BID)
    all_round_results.append(round_result)
    
    # Log this round's data
    logger.log_vignette_round(round_num, round_result)
    logger.log_agent_results(round_num, round_result, agents)
    logger.log_bids(round_num, round_result, agents)
    
    # Reset agents for next round
    for agent in agents:
        agent.reset_for_new_vignette()

# Summary
print("\n" + "="*70)
print("SIMULATION SUMMARY")
print("="*70)

total_correctness = sum(r['correctness'] for r in all_round_results) / len(all_round_results)
total_costs = sum(r['total_costs'] for r in all_round_results)
total_rewards = sum(r['total_rewards'] for r in all_round_results)

print(f"\nAverage Correctness:      {total_correctness:.1%}")
print(f"Total Costs (all rounds): ${total_costs:.4f}")
print(f"Total Rewards (all rounds): ${total_rewards:.4f}")

if total_costs > 0:
    efficiency = total_correctness / total_costs
    print(f"Efficiency (Correctness/Cost): {efficiency:.2f}")

print(f"\n📊 Key Insight:")
print(f"   Higher total rewards = more strategic, meaningful collaboration")
print(f"   (not just cost reduction, but correctness maintenance)")

# Agent-level analysis
print("\n" + "="*70)
print("AGENT PERFORMANCE BY COMMUNICATION STYLE")
print("="*70)

agent_stats = defaultdict(lambda: {'total_cost': 0.0, 'total_reward': 0.0, 'count': 0})

for round_result in all_round_results:
    for agent_id, agent_data in round_result['agents'].items():
        agent_obj = next((a for a in agents if a.agent_id == agent_id), None)
        if agent_obj:
            style = agent_obj.communication_style
            cost = round_result['costs_by_agent'][agent_id]
            reward = agent_data.get('reward', 0.0)
            
            agent_stats[style]['total_cost'] += cost
            agent_stats[style]['total_reward'] += reward
            agent_stats[style]['count'] += 1

for style in sorted(agent_stats.keys()):
    stats = agent_stats[style]
    avg_cost = stats['total_cost'] / stats['count'] if stats['count'] > 0 else 0
    avg_reward = stats['total_reward'] / stats['count'] if stats['count'] > 0 else 0
    print(f"\n{style.upper()}:")
    print(f"  Avg Cost per round:   ${avg_cost:.4f}")
    print(f"  Avg Reward per round: ${avg_reward:.4f}")
    print(f"  Net Benefit:          ${avg_reward - avg_cost:.4f}")

print("\n" + "="*70)
print("✓ Simulation Complete!")
print("="*70)

# Log final summaries
logger.log_agent_summary(all_round_results, agents)
logger.log_simulation_summary(all_round_results, agents)
logger.print_summary(all_round_results)
