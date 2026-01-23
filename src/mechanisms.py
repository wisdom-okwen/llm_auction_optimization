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
    
    Returns round_results dictionary matching auction format for logging
    """
    from collections import defaultdict, Counter
    import json
    
    vignette_id = vignette.get('id', 'unknown')
    round_results = {
        'vignette_id': vignette_id,
        'vignette_category': vignette.get('subcategory', ''),
        'agents': defaultdict(dict),
        'bids': {},
        'proposer': None,  # No designated proposer in free discussion
        'proposal': None,
        'interventions': defaultdict(list),
        'votes': defaultdict(list),
        'costs_by_agent': defaultdict(float),
    }
    
    # PHASE 1: PRIVATE ASSESSMENT (same as auction)
    for agent in agents:
        assessment = agent.assess(vignette)
        round_results['agents'][agent.agent_id]['assessment'] = assessment
    
    # PHASE 2: FREE DISCUSSION (all agents can propose)
    for agent in agents:
        assessment = round_results['agents'][agent.agent_id]['assessment']
        if assessment.get('option_choice') != 'Error: Unable to assess':
            proposal_result = agent.propose(vignette, assessment)
            round_results['costs_by_agent'][agent.agent_id] += proposal_result['cost']
    
    # PHASE 3: VOTING (all agents vote)
    options = vignette.get('options', [])
    if isinstance(options, str):
        try:
            options = json.loads(options)
        except:
            options = []
    
    votes = Counter()
    for agent in agents:
        assessment = round_results['agents'][agent.agent_id].get('assessment', {})
        vote = assessment.get('option_choice', options[0] if options else "No consensus")
        votes[vote] += 1
        round_results['votes'][agent.agent_id] = vote
    
    # PHASE 4: CONSENSUS & CORRECTNESS
    consensus_answer = votes.most_common(1)[0][0] if votes else "No consensus"
    consensus_votes = votes[consensus_answer]
    
    # Check correctness (from vignette correct_answer field)
    correct_answer = vignette.get('correct_answer', '')
    correctness = 1 if consensus_answer == correct_answer else 0
    
    # Calculate totals
    total_costs = sum(round_results['costs_by_agent'].values())
    total_rewards = len(agents) * 0.50 * correctness  # All agents get $0.50 if correct
    
    round_results['consensus_answer'] = consensus_answer
    round_results['consensus_votes'] = consensus_votes
    round_results['correctness'] = correctness
    round_results['total_costs'] = total_costs
    round_results['total_rewards'] = total_rewards
    
    return round_results
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
    - Agents take turns proposing in random order
    - Each proposer can make one proposal (costs tokens)
    - All agents vote at the end
    - Equal budget for all (no auction)
    
    Returns round_results dictionary matching auction format for logging
    """
    from collections import defaultdict, Counter
    import json
    
    vignette_id = vignette.get('id', 'unknown')
    round_results = {
        'vignette_id': vignette_id,
        'vignette_category': vignette.get('subcategory', ''),
        'agents': defaultdict(dict),
        'bids': {},
        'proposer': None,  # No single designated proposer
        'proposal': None,
        'interventions': defaultdict(list),
        'votes': defaultdict(list),
        'costs_by_agent': defaultdict(float),
    }
    
    # PHASE 1: PRIVATE ASSESSMENT
    for agent in agents:
        assessment = agent.assess(vignette)
        round_results['agents'][agent.agent_id]['assessment'] = assessment
    
    # PHASE 2: TURN-TAKING PROPOSALS
    agent_order = list(range(len(agents)))
    random.shuffle(agent_order)
    
    for turn, agent_idx in enumerate(agent_order):
        agent = agents[agent_idx]
        assessment = round_results['agents'][agent.agent_id]['assessment']
        if assessment.get('option_choice') != 'Error: Unable to assess':
            proposal_result = agent.propose(vignette, assessment)
            round_results['costs_by_agent'][agent.agent_id] += proposal_result['cost']
    
    # PHASE 3: VOTING (all agents vote)
    options = vignette.get('options', [])
    if isinstance(options, str):
        try:
            options = json.loads(options)
        except:
            options = []
    
    votes = Counter()
    for agent in agents:
        assessment = round_results['agents'][agent.agent_id].get('assessment', {})
        vote = assessment.get('option_choice', options[0] if options else "No consensus")
        votes[vote] += 1
        round_results['votes'][agent.agent_id] = vote
    
    # PHASE 4: CONSENSUS & CORRECTNESS
    consensus_answer = votes.most_common(1)[0][0] if votes else "No consensus"
    consensus_votes = votes[consensus_answer]
    
    # Check correctness
    correct_answer = vignette.get('correct_answer', '')
    correctness = 1 if consensus_answer == correct_answer else 0
    
    # Calculate totals
    total_costs = sum(round_results['costs_by_agent'].values())
    total_rewards = len(agents) * 0.50 * correctness  # All agents get $0.50 if correct
    
    round_results['consensus_answer'] = consensus_answer
    round_results['consensus_votes'] = consensus_votes
    round_results['correctness'] = correctness
    round_results['total_costs'] = total_costs
    round_results['total_rewards'] = total_rewards
    
    return round_results
