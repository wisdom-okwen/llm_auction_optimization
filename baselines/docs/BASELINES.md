# Baseline Mechanisms - Detailed Documentation

This document provides comprehensive documentation of baseline mechanisms in the LLM Auction project.

## Overview

The project compares three deliberation mechanisms:

1. **Sealed-Bid Auction** (main, in `scripts/run_simulation.py`) - Strategic incentive structure
2. **Free Discussion** (baseline, in `baselines/scripts/run_free_discussion.py`) - Unstructured collaboration
3. **Turn-Taking** (baseline, in `baselines/scripts/run_turn_taking.py`) - Structured equal participation

All mechanisms follow the same 5-phase structure per vignette:
- **Phase 1**: Private Assessment (agents evaluate independently)
- **Phase 2**: Deliberation (mechanism-specific)
- **Phase 3**: Proposals/Interventions (mechanism-specific)
- **Phase 4**: Voting (all agents vote)
- **Phase 5**: Payoff (correctness - costs)

---

## 1. Sealed-Bid Auction (Main Mechanism)

**Location**: `scripts/run_simulation.py`

**Key Characteristics:**
- Budget-constrained agents ($1.00 initial budget)
- Competitive bidding for proposer role (1st-price sealed-bid)
- Token price: $0.001 per LLM call
- Winner takes proposer role based on highest bid
- Communication styles affect bid strategy:
  - **Assertive**: 1.5× bid multiplier (aggressive, more likely to propose)
  - **Timid**: 0.5× bid multiplier (conservative, less likely to propose)
  - **Calibrated**: 1.0× multiplier (confidence-based bidding)
  - **Neutral**: 1.0× multiplier (baseline)

**Game Flow:**

1. **Phase 1 - Private Assessment** (0 cost)
   - Each agent independently evaluates vignette
   - Output: option choice, confidence (0-1), reasoning, key principles
   - Agents don't see others' assessments

2. **Phase 2 - Sealed-Bid Auction** (bid costs nothing, just deducted from budget)
   - Agents submit sealed bids: `bid_amount = confidence × style_multiplier × budget + noise`
   - Highest bidder wins proposer role
   - Winner's bid is deducted from their remaining budget

3. **Phase 3 - Proposal & Interventions** (token costs)
   - **Proposer** (bid winner): Crafts argument for their option (~60-100 tokens, costs $0.06-0.10)
   - **Non-proposers**: Can optionally pay to submit critiques (~60 tokens, costs $0.06)
   - Critiques can challenge proposal or raise ethical concerns

4. **Phase 4 - Voting** (0 cost)
   - All agents vote on best option
   - Majority vote determines final decision

5. **Phase 5 - Payoff Calculation** (0 cost)
   - If final vote = ethical consensus: agents earn $0.50
   - Costs deducted: (bid + proposal tokens + critique tokens) × token_price
   - **Net reward = $0.50 - total_costs**

**Research Question**: Does strategic incentive structure improve deliberation quality and cost-effectiveness compared to unstructured baselines?

**Run:**
```bash
python scripts/run_simulation.py
```

**Output**: `data/run_auction_YYYYMMDD_HHMMSS/`

---

## 2. Free Discussion (Baseline)

**Location**: `baselines/scripts/run_free_discussion.py`

**Key Characteristics:**
- **No auction mechanism** - all agents participate equally
- **No budget constraints** - agents can contribute freely
- **No strategic bidding** - no proposer role competition
- All agents can make proposals and critiques
- Represents unstructured collaborative decision-making

**Game Flow:**

1. **Phase 1 - Private Assessment** (0 cost)
   - Same as auction: each agent evaluates independently
   - Output: option choice, confidence, reasoning, principles

2. **Phase 2 - Free Discussion** (all agents can contribute, free)
   - All agents simultaneously make proposals (~100 tokens each)
   - No cost to participate
   - No limit on who can propose
   - Represents everyone having equal voice

3. **Phase 3 - Optional Critiques** (free)
   - Other agents can add critiques or counter-proposals
   - No cost, no budget deduction
   - Represents open debate without constraints

4. **Phase 4 - Voting** (0 cost)
   - All agents vote on best option
   - Majority vote = final decision

5. **Phase 5 - Payoff Calculation** (0 cost)
   - If final vote = ethical consensus: agents earn $0.50
   - **No costs deducted** (no budgeting in baselines)
   - **Net reward = $0.50** (always, if correct)

**Research Questions**: 
- Is unstructured discussion as effective as competitive bidding?
- Do cost-free contributions lead to more or less meaningful deliberation?
- How does participation compare?

**Run:**
```bash
python baselines/scripts/run_free_discussion.py
```

**Output**: `data/baselines/run_baseline_free_discussion_YYYYMMDD_HHMMSS/`

---

## 3. Turn-Taking (Baseline)

**Location**: `baselines/scripts/run_turn_taking.py`

**Key Characteristics:**
- **Structured turn order** - agents propose in random sequence
- **No auction** - turns determined by randomization, not bidding
- **No budget constraints** - agents can contribute freely
- **Guaranteed equal participation** - each agent gets exactly one turn to propose
- Represents structured round-robin deliberation

**Game Flow:**

1. **Phase 1 - Private Assessment** (0 cost)
   - Same as others: each agent evaluates independently

2. **Phase 2 - Turn-Taking Proposals** (all agents propose in turn order, free)
   - Random turn order generated
   - Agent 1 makes proposal (~100 tokens)
   - Agent 2 makes proposal (~100 tokens)
   - ...and so on for all 20 agents
   - No cost to participate
   - All agents guaranteed opportunity to propose

3. **Phase 3 - Open Discussion** (free)
   - After all proposals, open discussion allowed
   - Agents can add reactions or counter-proposals
   - No cost deductions

4. **Phase 4 - Voting** (0 cost)
   - All agents vote on best option
   - Majority vote = final decision

5. **Phase 5 - Payoff Calculation** (0 cost)
   - If final vote = ethical consensus: agents earn $0.50
   - **No costs deducted** (no budgeting)
   - **Net reward = $0.50** (always, if correct)

**Research Questions**:
- Is structured turn-taking as effective as competitive bidding?
- Does guaranteed participation lead to more diverse perspectives?
- How do turn-taking and bidding compare in deliberation quality?

**Run:**
```bash
python baselines/scripts/run_turn_taking.py
```

**Output**: `data/baselines/run_baseline_turn_taking_YYYYMMDD_HHMMSS/`

---

## Comparative Table

| Aspect | Auction | Free Discussion | Turn-Taking |
|--------|---------|-----------------|-------------|
| **Mechanism** | Sealed-bid 1st-price | No auction | Randomized turn order |
| **Proposer Selection** | Highest bid | All can propose | Turn order |
| **Budget Constraint** | Yes ($1.00/agent) | No | No |
| **Bidding** | Competitive | N/A | N/A |
| **Participation** | Strategic (some may not contribute) | Free/open (all can contribute) | Guaranteed (structured order) |
| **Cost Model** | Bids + tokens | Free | Free |
| **Reward if Correct** | $0.50 - costs | $0.50 | $0.50 |
| **Reward if Wrong** | -costs | $0.00 | $0.00 |
| **Expected Diversity** | Depends on bidding | High (all speak) | High (all turn) |
| **Communication Styles** | Affect bidding (multiplier) | Don't affect participation | Don't affect turn order |

---

## Running Comparisons

### Run All Mechanisms

```bash
# Main auction
python scripts/run_simulation.py

# Baselines
python baselines/scripts/run_all_baselines.py

# Analyze (within baselines)
python baselines/scripts/analyze_baselines.py
```

### Data Output Structure

```
data/
├── run_auction_20260123_120000/
│   ├── vignette_results.csv
│   ├── agent_round_results.csv
│   ├── bid_data.csv
│   ├── agent_summary.csv
│   └── simulation_summary.csv
└── baselines/
    ├── run_baseline_free_discussion_20260123_130000/
    │   ├── vignette_results.csv
    │   ├── agent_round_results.csv
    │   ├── bid_data.csv (empty)
    │   ├── agent_summary.csv
    │   └── simulation_summary.csv
    └── run_baseline_turn_taking_20260123_140000/
        ├── vignette_results.csv
        ├── agent_round_results.csv
        ├── bid_data.csv (empty)
        ├── agent_summary.csv
        └── simulation_summary.csv
```

---

## Key Metrics for Comparison

### Correctness
- **Definition**: % of vignettes where final vote matches ethical consensus
- **By Mechanism**: Does auction/discussion/turn-taking achieve better accuracy?
- **By Style**: Which communication styles contribute to correctness?

### Cost Efficiency (Auction Only)
- **Total Cost**: Sum of all bids + all tokens × token_price
- **Cost/Round**: Average cost per vignette
- **Cost/Agent**: Average per-agent spending

### Reward Performance
- **Total Reward**: Sum of (correctness_bonus - costs) across all agents
- **Average Reward/Agent**: Mean per-agent net payout
- **Reward Distribution**: How fair? Do some exploit, others lose?

### Deliberation Quality
- **Participation**: Number of agents who proposed/critiqued
- **Proposals/Agent**: Average proposals per agent
- **Diversity**: Do all communication styles participate equally?

---

## Analysis Examples

### Compare Correctness Across Mechanisms

```python
import pandas as pd

# Load results
auction = pd.read_csv('data/run_auction_*/agent_round_results.csv')
free = pd.read_csv('data/baselines/run_baseline_free_discussion_*/agent_round_results.csv')
turn = pd.read_csv('data/baselines/run_baseline_turn_taking_*/agent_round_results.csv')

# Correctness by mechanism
for name, df in [('Auction', auction), ('Free', free), ('Turn', turn)]:
    correct = (df['option_choice'] == df['expected_reasoning']).mean()
    print(f"{name}: {correct:.1%}")
```

### Compare Costs (Auction) vs. Rewards (Baselines)

```python
# Auction costs
auction_total_cost = auction['total_cost'].sum()
auction_avg_reward = (auction['reward']).mean()

# Baselines (no costs)
free_avg_reward = free['reward'].mean()
turn_avg_reward = turn['reward'].mean()

print(f"Auction: Total Cost=${auction_total_cost:.2f}, Avg Reward=${auction_avg_reward:.2f}")
print(f"Free:    Avg Reward=${free_avg_reward:.2f}")
print(f"Turn:    Avg Reward=${turn_avg_reward:.2f}")
```

### Communication Style Effects

```python
for mechanism, df in [('Auction', auction), ('Free', free), ('Turn', turn)]:
    print(f"\n{mechanism}:")
    for style in ['assertive', 'timid', 'calibrated', 'neutral']:
        subset = df[df['communication_style'] == style]
        correctness = (subset['option_choice'] == subset['expected_reasoning']).mean()
        avg_cost = subset['total_cost'].mean()
        print(f"  {style}: {correctness:.1%} correct, ${avg_cost:.3f} avg cost")
```

---

## Hypotheses

1. **Strategic incentives improve accuracy**: Auction mechanism incentivizes meaningful participation and higher correctness than free discussion
2. **Cost-effectiveness**: Auction achieves similar correctness to baselines but at lower total cost
3. **Communication styles matter**: Assertive agents more likely to propose in auction; participation equal in baselines
4. **Diversity improves reasoning**: Turn-taking's guaranteed participation leads to better reasoning than free discussion's self-selected participation

---

## Future Extensions

1. **Token Price Sweep**: Run all mechanisms at different token prices (0.0001 to 0.01)
2. **Agent Count Sensitivity**: Test with 5, 10, 15, 20, 25 agents
3. **Budget Sensitivity**: Vary initial budget ($0.10 to $2.00)
4. **Hybrid Mechanisms**: Combine auction + turn-taking features
5. **Domain Generalization**: Test on different vignette types/domains

---

## References

- Sealed-bid auctions: classic mechanism design theory
- Multi-agent reasoning: council debates, mixture-of-experts
- Communication cost: models of constrained group deliberation
- Ethical reasoning: team-based healthcare ethics consultations
