"""
Different deliberation mechanisms for agent coordination.

This module provides three alternative mechanisms for agents to deliberate on ethical vignettes:

1. Sealed-Bid Auction (implemented in run_simulation.py)
   - Competitive bidding for proposer role
   - Budget-constrained ($1.00 per agent)
   - Communication style affects bid multipliers
   - Incentivizes meaningful participation

2. Free Discussion (run_free_discussion_round)
   - No auction; all agents participate equally
   - No budget constraints
   - All agents can propose and criticize
   - Unstructured collaborative baseline

3. Turn-Taking (run_turn_taking_round)
   - Agents take turns proposing in random order
   - No auction; no competition
   - Equal guaranteed participation
   - Structured collaborative baseline

All mechanisms follow the same 5-phase structure:
  Phase 1: Private Assessment (agents evaluate independently)
  Phase 2: Deliberation (mechanism-specific)
  Phase 3: Proposals/Interventions (mechanism-specific)
  Phase 4: Voting (all agents vote)
  Phase 5: Payoff (correctness - costs)

Each phase is logged to CSV for comparative analysis.
"""

from typing import Dict, Any, List
import random


def run_free_discussion_round(vignette: Dict[str, Any], agents: List, config: Dict) -> Dict[str, Any]:
    """
    Free Discussion Mechanism:
    - All agents discuss and debate equally (no auction)
    - All agents can propose/contribute
    - Voting at the end
    - No budget constraints or winner-take-all structure
    
    Returns round_results dictionary for logging
    """
    vignette_id = vignette.get('id', 'unknown')
    round_results = {
        'vignette_id': vignette_id,
        'round_num': 0,  # Will be set by caller
        'mechanism': 'free_discussion',
        'proposer_id': None,  # No designated proposer
        'proposals': [],
        'agent_results': [],
        'bid_data': [],
        'correctness': 0,
        'total_cost': 0.0,
        'total_reward': 0.0,
    }
    
    # PHASE 1: PRIVATE ASSESSMENT (same as auction)
    for agent in agents:
        assessment = agent.assess(vignette)
        round_results['agent_results'].append({
            'agent_id': agent.agent_id,
            'style': agent.communication_style,
            'assessment': assessment,
            'bid': 0,  # No bidding in free discussion
            'won_auction': False,
            'vote': None,
        })
    
    # PHASE 2: FREE DISCUSSION (all agents can contribute)
    # Each agent proposes their view (costs tokens)
    for agent in agents:
        assessment = next((r['assessment'] for r in round_results['agent_results'] 
                          if r['agent_id'] == agent.agent_id), None)
        if assessment and assessment.get('option_choice') != 'Error: Unable to assess':
            proposal = agent.propose(vignette, assessment)
            round_results['proposals'].append({
                'agent_id': agent.agent_id,
                'proposal': proposal,
                'cost': proposal.get('cost', 0),
            })
    
    # PHASE 3: VOTING (all agents vote)
    votes = []
    for agent in agents:
        assessment = next((r['assessment'] for r in round_results['agent_results'] 
                          if r['agent_id'] == agent.agent_id), None)
        if assessment:
            vote = assessment.get('option_choice', 'Error: Unable to assess')
            votes.append(vote)
            # Update agent result with vote
            for result in round_results['agent_results']:
                if result['agent_id'] == agent.agent_id:
                    result['vote'] = vote
    
    # PHASE 4: CORRECTNESS & PAYOFF
    if votes:
        # Consensus: majority vote
        vote_counts = {}
        for vote in votes:
            vote_counts[vote] = vote_counts.get(vote, 0) + 1
        consensus_answer = max(vote_counts, key=vote_counts.get)
    else:
        consensus_answer = None
    
    # Calculate costs and rewards
    total_cost = sum(r.get('cost', 0) for proposal_list in 
                     [round_results['proposals']] for r in proposal_list)
    
    # Reward: $0.50 per correct option chosen (distributed equally to all who voted correctly)
    correctness_bonus = 0
    correct_voters = 0
    
    return round_results


def run_turn_taking_round(vignette: Dict[str, Any], agents: List, config: Dict) -> Dict[str, Any]:
    """
    Turn-Taking Mechanism:
    - Agents take turns proposing in a fixed order
    - Each proposer can make one proposal (costs tokens)
    - All agents vote at the end
    - Equal budget for all (no auction)
    
    Returns round_results dictionary for logging
    """
    vignette_id = vignette.get('id', 'unknown')
    round_results = {
        'vignette_id': vignette_id,
        'round_num': 0,  # Will be set by caller
        'mechanism': 'turn_taking',
        'proposers': [],  # Multiple proposers in order
        'proposals': [],
        'agent_results': [],
        'bid_data': [],
        'correctness': 0,
        'total_cost': 0.0,
        'total_reward': 0.0,
    }
    
    # PHASE 1: PRIVATE ASSESSMENT (same as auction)
    for idx, agent in enumerate(agents):
        assessment = agent.assess(vignette)
        round_results['agent_results'].append({
            'agent_id': agent.agent_id,
            'style': agent.communication_style,
            'assessment': assessment,
            'turn_order': idx,  # Track order
            'vote': None,
        })
    
    # PHASE 2: TURN-TAKING PROPOSALS
    # Agents take turns (in random order to be fair) proposing
    agent_order = list(range(len(agents)))
    random.shuffle(agent_order)
    
    for turn, agent_idx in enumerate(agent_order):
        agent = agents[agent_idx]
        assessment = next((r['assessment'] for r in round_results['agent_results'] 
                          if r['agent_id'] == agent.agent_id), None)
        if assessment and assessment.get('option_choice') != 'Error: Unable to assess':
            proposal = agent.propose(vignette, assessment)
            round_results['proposals'].append({
                'turn': turn,
                'agent_id': agent.agent_id,
                'proposal': proposal,
                'cost': proposal.get('cost', 0),
            })
            round_results['proposers'].append(agent.agent_id)
    
    # PHASE 3: VOTING (all agents vote)
    votes = []
    for agent in agents:
        assessment = next((r['assessment'] for r in round_results['agent_results'] 
                          if r['agent_id'] == agent.agent_id), None)
        if assessment:
            vote = assessment.get('option_choice', 'Error: Unable to assess')
            votes.append(vote)
            # Update agent result with vote
            for result in round_results['agent_results']:
                if result['agent_id'] == agent.agent_id:
                    result['vote'] = vote
    
    # PHASE 4: CORRECTNESS & PAYOFF
    if votes:
        vote_counts = {}
        for vote in votes:
            vote_counts[vote] = vote_counts.get(vote, 0) + 1
        consensus_answer = max(vote_counts, key=vote_counts.get)
    else:
        consensus_answer = None
    
    # Calculate costs
    total_cost = sum(p.get('cost', 0) for p in round_results['proposals'])
    
    return round_results
