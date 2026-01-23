#!/usr/bin/env python
"""
Run FREE DISCUSSION baseline (no auction mechanism).
Agents discuss and vote equally without budget constraints or winner selection.
"""

import os
import sys
import json
import random
from collections import Counter, defaultdict
import pandas as pd
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add paths for imports (../../ to get to project root)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.agents import Agent, MockAgent
from src.mechanisms import run_free_discussion_round
from src.data_logger import SimulationLogger

# Check for OpenAI API key
use_real_openai = os.environ.get('PERSONAL_OPENAI_KEY', '').startswith('sk-')

if use_real_openai:
    print("✓ Valid OpenAI API key detected - using real agents")
else:
    print("⚠️  Using MOCK agents (no real OpenAI calls)")
    print()

# Load dataset
print("\n" + "="*70)
print("FREE DISCUSSION BASELINE")
print("="*70)
print("\nSTEP 1: Load Ethical Healthcare Vignettes")
print("="*70)

df_vignettes = pd.read_csv('datasets/Ethical-Reasoning-in-Mental-Health.csv')
print(f"✓ Loaded {len(df_vignettes)} ethical healthcare vignettes")

# Sample 5 vignettes for testing
n_vignettes = 5
sampled_indices = random.sample(range(len(df_vignettes)), n_vignettes)
sample_vignettes = df_vignettes.iloc[sampled_indices].to_dict('records')

print(f"✓ Selected {n_vignettes} vignettes:")
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
print(f"Mechanism: Free Discussion (no auction)")

# Initialize data logger
logger = SimulationLogger(data_dir="data/baselines", mechanism='baseline_free_discussion')

# Run simulation
print("\n" + "="*70)
print("STEP 3: Run Free Discussion Rounds")
print("="*70)

config = {
    'token_price': 0.001,
    'initial_budget': 1.0,
}

for round_num, vignette in enumerate(sample_vignettes, 1):
    print(f"\nRound {round_num}/{n_vignettes}: {vignette.get('subcategory', 'Unknown')}")
    
    # Reset agents for new vignette
    for agent in agents:
        agent.reset_for_new_vignette()
    
    # Run free discussion round
    results = run_free_discussion_round(vignette, agents, config)
    results['round_num'] = round_num
    
    # Log results
    logger.log_vignette_round(results)
    
    # Extract and log agent results
    for agent_result in results.get('agent_results', []):
        agent_id = agent_result.get('agent_id')
        agent = next((a for a in agents if a.agent_id == agent_id), None)
        if agent:
            logger.log_agent_result(
                round_num=round_num,
                vignette_id=vignette.get('id'),
                agent=agent,
                assessment=agent_result.get('assessment'),
                bid=0,  # No bidding in free discussion
                won_proposal=False,
                vote=agent_result.get('vote'),
                proposal_cost=0,
                intervention_cost=0,
                agent_style=agent.communication_style
            )
    
    # Log bids (empty for free discussion)
    logger.log_bids(round_num, vignette.get('id'), [])
    
    print(f"  ✓ Round complete - {len(results.get('proposals', []))} proposals made")

# Log agent summary
print("\n" + "="*70)
print("STEP 4: Generate Summary Statistics")
print("="*70)

agent_summary = []
for agent in agents:
    agent_summary.append({
        'agent_id': agent.agent_id,
        'communication_style': agent.communication_style,
        'total_tokens_used': agent.total_tokens_used,
        'total_tokens_cost': agent.total_tokens_used * config['token_price'],
    })

logger.log_agent_summary(agent_summary)

# Log simulation summary
simulation_summary = {
    'mechanism': 'free_discussion',
    'n_agents': len(agents),
    'n_vignettes': len(sample_vignettes),
    'total_agent_cost': sum(a['total_tokens_cost'] for a in agent_summary),
    'using_real_agents': use_real_openai,
}

logger.log_simulation_summary(simulation_summary)

print(f"\n✓ Simulation complete!")
print(f"✓ Data logged to: {logger.run_dir}")
print(f"\nFiles generated:")
print(f"  - vignette_results.csv")
print(f"  - agent_round_results.csv")
print(f"  - bid_data.csv")
print(f"  - agent_summary.csv")
print(f"  - simulation_summary.csv")
