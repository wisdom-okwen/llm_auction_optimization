# Baseline Mechanisms

This directory contains implementations of two baseline deliberation mechanisms for comparison against the main sealed-bid auction:

## Baselines

1. **Free Discussion** - Unstructured collaborative baseline
   - All agents discuss equally
   - No auction or budget constraints
   - Run: `python scripts/run_free_discussion.py`

2. **Turn-Taking** - Structured equal participation baseline
   - Agents take turns proposing in random order
   - No auction or competition
   - Run: `python scripts/run_turn_taking.py`

## Running Baselines

**Run all baselines:**
```bash
python scripts/run_all_baselines.py
```

**Run individually:**
```bash
python scripts/run_free_discussion.py
python scripts/run_turn_taking.py
```

**Analyze results:**
```bash
python scripts/analyze_baselines.py
```

## Data Output

All baseline results are saved to `../data/baselines/`:
- `run_baseline_free_discussion_YYYYMMDD_HHMMSS/`
- `run_baseline_turn_taking_YYYYMMDD_HHMMSS/`

Each contains:
- `vignette_results.csv` - Per-vignette results
- `agent_round_results.csv` - Per-agent-per-round details
- `bid_data.csv` - Bidding information (empty for baselines)
- `agent_summary.csv` - Aggregate statistics
- `simulation_summary.csv` - Overall mechanism performance

## Comparison

Compare baseline results to main auction in `../data/`:
```bash
# Compare a baseline run against auction runs
python scripts/analyze_baselines.py
```

Key metrics:
- **Correctness**: % of vignettes with correct consensus
- **Cost**: Average tokens spent per agent
- **Reward**: Payout after costs
- **Efficiency**: Correctness per dollar

## Architecture

```
baselines/
├── scripts/
│   ├── run_free_discussion.py      # Free discussion baseline
│   ├── run_turn_taking.py          # Turn-taking baseline
│   ├── run_all_baselines.py        # Run both
│   └── analyze_baselines.py        # Compare and analyze
├── docs/
│   └── README.md                   # This file
└── data/                           # (symlink to ../data/baselines/)
```

## Implementation Details

Both baselines:
- Use same 20 agents (5 of each communication style)
- Evaluate same 5 test vignettes
- Generate identical CSV outputs
- Support both real OpenAI agents and mock agents
- Log to `data/baselines/` with mechanism-specific naming

See main docs for full mechanism specifications.
