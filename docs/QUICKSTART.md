# Quick Start Guide

## Installation

1. **Activate virtual environment**:
   ```bash
   cd /llm_auction_optimization
   source .venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the MVP Demo

The fastest way to see the system in action:

```bash
# Launch Jupyter
jupyter notebook

# Open LLM_Auction_MVP_Demo.ipynb
# Run all cells to see:
# - 3-5 ethical healthcare vignettes (from dataset of 50)
# - 20 agents with different communication styles
# - Sealed-bid auction mechanics
# - Vote and payoff calculation
# - Results visualization
```

**Runtime**: ~5-10 minutes for full demo with 3-5 vignettes × 20 agents.

## Project Structure

```
llm_auction_optimization/
├── config.py               # Experiment configurations
├── types.py                # Data structures (ClinicalVignette, AgentState, RoundOutcome, etc.)
├── auctions.py             # Auction mechanisms (sealed-bid, Vickrey, all-pay)
├── utils.py                # Logging, metrics, and visualization helpers
├── __init__.py             # Package exports
├── LLM_Auction_MVP_Demo.ipynb  # Interactive demo notebook
├── DESIGN.md               # Detailed design document (game mechanics, pseudocode)
├── README.md               # Project overview and methodology
├── requirements.txt        # Python dependencies
└── results/                # Output directory for experiment logs (auto-created)
```

## Key Files

### For Understanding the Project
- **README.md**: Start here for overview, research question, and baseline comparisons
- **DESIGN.md**: Detailed game mechanics, pseudocode, experimental conditions, and implementation roadmap

### For Running Experiments
- **config.py**: Define experiment conditions (baselines, token prices, budgets, agent styles)
- **LLM_Auction_MVP_Demo.ipynb**: Interactive demo with mock agents

### For Integration
- **types.py**: Import `ClinicalVignette`, `RoundOutcome`, `AgentState` for your own experiments
- **auctions.py**: Use `run_auction()` to implement sealed-bid, Vickrey, or all-pay auctions
- **utils.py**: Use `ExperimentLogger`, `ExperimentMetrics`, `MetricsDisplay` for analysis

## Quick Development Workflow

### Step 1: Understand the Mechanics
```bash
# Read DESIGN.md to see the full game flow and payoff structure
# Run the MVP notebook to see it in action
```

### Step 2: Add Real LLMs (Next Iteration)
Create a new `agents.py` file with a real LLM agent:
```python
from llm_auction_optimization import PrivateAssessment
from openai import OpenAI

class LLMClinicalAgent:
    def __init__(self, agent_id, model="gpt-4"):
        self.agent_id = agent_id
        self.client = OpenAI()
        self.model = model
    
    def assess(self, vignette):
        # Call LLM with clinical prompt
        # Parse response to get action, confidence, rationale
        # Return PrivateAssessment object
        pass
```

### Step 3: Run Real Experiments
```python
from llm_auction_optimization import ExperimentConfig, ExperimentLogger
from agents import LLMClinicalAgent
import json

# Load dataset
from datasets import load_dataset
hf_data = load_dataset('UVSKKR/Ethical-Reasoning-in-Mental-Health-v1')

# Run experiments
conditions = [
    ExperimentConfig(baseline='free_discussion'),
    ExperimentConfig(baseline='turn_taking'),
    ExperimentConfig(baseline='auction', token_price=0.001),
    ExperimentConfig(baseline='auction', token_price=0.0005),  # Price sweep
]

results = {}
for config in conditions:
    logger = ExperimentLogger()
    outcomes = []
    
    for vignette in hf_data['test'][:10]:  # Run on 10 vignettes
        agents = [LLMClinicalAgent(f'Agent_{i}') for i in range(5)]
        outcome = run_clinical_auction_round(agents, vignette, config)
        outcomes.append(outcome)
        logger.log_round(outcome)
    
    filepath = logger.save(f"experiment_{config.baseline}_{config.token_price}.json")
    results[config.label] = ExperimentMetrics.compute_metrics(outcomes)

# Analyze and visualize
for label, metrics in results.items():
    MetricsDisplay.print_summary(metrics)
```

### Step 4: Visualize Results
```python
import matplotlib.pyplot as plt
import pandas as pd

# Load results from different token prices
prices = [0.0001, 0.0005, 0.001, 0.005]
accuracies = [...]  # From each experiment
costs = [...]

# Plot accuracy vs cost
plt.figure(figsize=(10, 6))
plt.scatter(costs, accuracies, s=100)
plt.xlabel('Total Communication Cost ($)')
plt.ylabel('Accuracy (%)')
plt.title('Accuracy-Cost Tradeoff: Finding the Sweet Spot')
plt.grid(alpha=0.3)
plt.savefig('results/accuracy_vs_cost.png')
```

## Experiment Conditions (From DESIGN.md)

| Condition | Baseline | Token Price | Budget | Notes |
|-----------|----------|-------------|--------|-------|
| A1 | Free discussion | — | — | Highest accuracy, highest cost |
| B1 | Turn-taking | — | 1.00 | Structured; controlled cost |
| C1 | **Auction** | **0.001** | **1.00** | **MVP baseline** |
| C3-C4 | Auction | 0.0005–0.005 | 1.00 | **Token price sweep** |
| C5-C6 | Auction | 0.001 | 0.50–2.00 | Budget sweep |

Run C1, B1, A1 first to validate baselines, then do price sweep (C3-C4) for main results.

## Contact & Support

For questions about the experiment design, see **DESIGN.md**.  
For issues with the codebase, check **README.md** dependencies and GPU/model setup.

---

**Hackathon Goal**: Demonstrate that budgeted communication + auctions can maintain accuracy while cutting communication cost by 50%+.

**Expected Finding**: "Sweet spot" price where teams remain effective but efficient.
