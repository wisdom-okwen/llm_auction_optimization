#!/usr/bin/env python
"""
Run TURN-TAKING baseline (agents take turns proposing).
Agents deliberate in fixed turn order without auction mechanism or budget constraints.
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
from src.mechanisms import run_turn_taking_round
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
print("TURN-TAKING BASELINE")
print("="*70)
print("\nSTEP 1: Load Ethical Healthcare Vignettes")
print("="*70)

# Get absolute path to dataset
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
dataset_path = os.path.join(project_root, 'datasets/Ethical-Reasoning-in-Mental-Health.csv')
df_vignettes = pd.read_csv(dataset_path)
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
print(f"Mechanism: Turn-Taking (agents propose in sequence)")

# Initialize data logger with absolute path
data_dir = os.path.join(project_root, 'data/baselines')
logger = SimulationLogger(data_dir=data_dir, mechanism='baseline_turn_taking')

# Run simulation
print("\n" + "="*70)
print("STEP 3: Run Turn-Taking Rounds")
print("="*70)

config = {
    'token_price': 0.001,
    'initial_budget': 1.0,
}

all_round_results = []

for round_num, vignette in enumerate(sample_vignettes, 1):
    print(f"\nRound {round_num}/{n_vignettes}: {vignette.get('subcategory', 'Unknown')}")
    
    # Reset agents for new vignette
    for agent in agents:
        agent.reset_for_new_vignette()
    
    # Run turn-taking round
    results = run_turn_taking_round(vignette, agents, config)
    all_round_results.append(results)
    
    # Log results
    logger.log_vignette_round(round_num, results)
    logger.log_agent_results(round_num, results, agents)
    logger.log_bids(round_num, results, agents)
    
    print(f"  ✓ Round complete - {len(results.get('proposals', []))} agents proposed in turn")

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

logger.log_agent_summary(all_round_results, agents)

# Log simulation summary
simulation_summary = {
    'mechanism': 'baseline_turn_taking',
    'n_agents': len(agents),
    'n_vignettes': len(sample_vignettes),
    'total_agent_cost': sum(a['total_tokens_cost'] for a in agent_summary),
    'using_real_agents': use_real_openai,
}

logger.log_simulation_summary(all_round_results, agents)

print(f"\n✓ Simulation complete!")
print(f"✓ Data logged to: {logger.run_dir}")
print(f"\nFiles generated:")
print(f"  - vignette_results.csv")
print(f"  - agent_round_results.csv")
print(f"  - bid_data.csv")
print(f"  - agent_summary.csv")
print(f"  - simulation_summary.csv")
