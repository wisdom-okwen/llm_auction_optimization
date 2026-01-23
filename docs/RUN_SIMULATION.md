# Running the LLM Auction Optimization Simulation

## Quick Start (OpenAI Real Agents)

### Prerequisites

1. **Set your OpenAI API key**:
   ```bash
   export OPENAI_API_KEY='sk-...'
   ```

2. **Activate environment**:
   ```bash
   cd /playpen-ssd/wokwen/projects/llm_auction_optimization
   source .venv/bin/activate
   ```

3. **Install/verify dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Run the Notebook

```bash
jupyter notebook MVP_Demo_OpenAI.ipynb
```

This will:
- Create 20 OpenAI-powered agents with different communication styles (assertive, timid, calibrated, neutral)
- Load 3-5 real ethical healthcare vignettes from the dataset
- Run a complete auction simulation:
  - **Phase 1**: Private assessment (each agent independently evaluates)
  - **Phase 2**: Sealed-bid auction (agents bid for proposer role)
  - **Phase 3**: Proposal & optional critiques (winner proposes, others can pay to intervene)
  - **Phase 4**: Voting (agents vote on final answer)
  - **Phase 5**: Payoff (rewards distributed, costs deducted)
- Visualize results (correctness, costs, agent performance by style)

**Runtime**: ~10-20 min per vignette (slower first time due to model loading)

## Using Mock Agents (For Testing)

To test without OpenAI API calls, set this in the notebook:

```python
use_real_openai = False  # Uses MockAgent instead
```

Mock agents run instantly for prototyping, but provide deterministic random responses instead of real reasoning.

## Key Files

- **MVP_Demo_OpenAI.ipynb**: Complete end-to-end simulation notebook (recommended)
- **agents.py**: Agent implementations (Agent = OpenAI, MockAgent = testing, LocalLLMAgent = Qwen)
- **config.py**: Experiment configurations (20 agents, token pricing, auction types)
- **auctions.py**: Auction mechanism implementations
- **Ethical-Reasoning-in-Mental-Health.csv**: 50 real ethical healthcare vignettes

## Configuration Options

In `config.py`:
- `n_agents`: Number of agents (default: 20)
- `token_price`: Cost per token (default: 0.001, varies 0.0001-0.01 for sweep)
- `auction_type`: "sealed_bid" (default), "vickrey", "all_pay"
- `communication_styles`: "assertive", "timid", "calibrated", "neutral"

## Expected Output

After running, you'll see:
```
Average Correctness:  85%
Total Costs (all rounds):  $0.2345
Total Rewards (all rounds): $8.7654
Efficiency: 36.32

Agent-Level Performance by Communication Style
ASSERTIVE:
  Avg Cost:     $0.0150
  Avg Reward:   $0.4320
  Net Benefit:  $0.4170

TIMID:
  Avg Cost:     $0.0045
  Avg Reward:   $0.2850
  Net Benefit:  $0.2805

[... etc]
```

**Key Insight**: If total rewards is high relative to costs while maintaining correctness, the mechanism successfully incentivizes meaningful collaboration rather than silence or random bidding.

## Next Steps

1. **Token Price Sweep**: Run across token_price values [0.0001, 0.0005, 0.001, 0.005, 0.01] and plot correctness vs cost
2. **Scale to Full Dataset**: Use all 50 vignettes for statistical robustness
3. **Baseline Comparison**: Compare against free_discussion and turn_taking baselines
4. **Communication Analysis**: Analyze which agent styles perform best under different price conditions
