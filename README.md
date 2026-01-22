# LLM Collectives with Budgeted Communication

## Summary

**Budgeted LLM Council for Ethical Healthcare Decisions:** We simulate a committee of advisor LLM agents making ethical decisions on mental health vignettes where communication is costly. Each agent has a limited monetary budget and must spend budget to (1) bid for proposal rights and (2) pay per token to contribute messages. After a sealed-bid auction selects the proposer, other agents may pay to submit concise critiques or alternative perspectives before a group vote determines the final decision. Agents earn rewards only when the final decision matches the ethical consensus, creating incentives to speak only when marginal information value exceeds cost. We evaluate correctness–cost tradeoffs against free-discussion and structured turn-taking baselines, sweeping token prices and budgets.

---

## Research Question

**How do token-priced communication and market mechanisms (bidding for influence) change multi-agent ethical decision-making accuracy and total communication cost?**

## Core Idea

Agents act as advisors (clinicians, ethicists, patient advocates) with **limited budgets**. Every token spoken costs money. Agents can also spend money to increase the chance their proposed resolution becomes the group's decision. Agents earn rewards **only if the final decision matches the ethical consensus**, so they must spend strategically. This forces meaningful participation: speaking/bidding only makes sense if it increases chance of correctness enough to justify cost. **Mimics real healthcare teams where time/attention is scarce and interventions must justify their cost.**

## Primary Outcomes

- **Correctness**: Did the final group decision match the ethical consensus (expected reasoning)?
- **Cost**: Total tokens spent × token price + bids paid
- **Efficiency**: Correctness per dollar (or correctness at fixed budget)
- **Deliberation quality**: How many agents contributed meaningful critiques or perspectives?

---

## Game Mechanics (MVP)

### Setup

- **Task**: Ethical healthcare vignette → select best resolution
  - Confidentiality vs disclosure dilemmas
  - Autonomy vs beneficence (adult & minor cases)
  - Bias in AI systems (detection & correction)
  - Multiple-choice ethical options with ground-truth consensus
- **N agents**: e.g., 5 LLM instances acting as advisors (clinicians, ethicists, patient advocates)
- **Initial budget B**: e.g., $1.00 per agent (represents cognitive load / meeting time)
- **Token price p**: e.g., $0.001/token (models communication cost in team deliberation)

### Round 0: Private Assessment

Each agent independently produces:
- **Recommended resolution** `a_i` (choice from 4-5 options, e.g., "Honor confidentiality vs Inform parents vs Joint conversation")
- **Confidence** `c_i ∈ [0,1]` (in their recommendation)
- **Ethical rationale** (1–3 bullet points: key principles, stakeholder perspectives, or reasoning)

Agents **do not** see others' assessments yet.

### Round 1: Sealed-Bid Auction (Proposal Rights)

Each agent submits a sealed bid `b_i ≤ remaining_budget_i` to be the **proposer** (the advisor whose recommendation is shown first as the candidate group decision).

- **Highest bidder wins** and becomes proposer
- **Winner pays their bid** (cost deducted from budget)
- Everyone sees proposer's recommended resolution + ethical rationale

### Round 2: Optional Paid Interventions

Non-proposers choose to:
- **Speak** (pay per token) to critique the proposal, suggest alternative resolution, or raise ethical concern, OR
- **Stay silent** (pay nothing)

**MVP constraint**: One short message max per agent (≤60 tokens). Examples:
  - "This misses the principle of respecting adolescent autonomy"
  - "Alternative: involve the patient in a joint conversation with parents"
  - "Failing to address bias in the AI training data perpetuates harm"

### Round 3: Vote

Agents vote on the best resolution among those shown. Simple majority wins.

### Payoff (Real Incentives)

- **If final decision matches consensus**: Each agent earns reward `R` (e.g., +$0.50) **minus** what they spent (bids + token costs)
- **If final decision is wrong**: No reward, but still pay costs
- **Optional bonus**: Agent whose critique or intervention led to correct final decision gets +bonus (credit for meaningful contribution)

---

## What to Compare (Baselines + Variants)

### Baseline A: Free Discussion
- All agents share recommendations + reasoning; vote
- No budget, no token cost
- Expected: Highest accuracy, highest communication cost (realistic for unmanaged team meetings)

### Baseline B: Structured Turn-Taking, No Auction
- Round-robin: each agent gets exactly 1 short message
- Token cap but no bidding
- Expected: Medium accuracy, controlled cost (like formal ethics committee rounds)

### Your Method: Auction + Token Cost
- Sealed-bid proposer + optional paid critiques; vote
- Expected: Strategic participation, balanced accuracy/cost, meaningful interventions

### Experimental Variants

We will systematically test all combinations of the following knobs:

| Knob | Values | Effect |
|------|--------|--------|
| Token price `p` | Low (0.0005), Medium (0.001), High (0.005) | Sparse vs verbose discussion |
| Budget `B` | Tight (0.50), Medium (1.00), Loose (2.00) | Constrained vs permissive bidding |
| Auction type | Sealed-bid vs Vickrey (2nd-price) | Winner pays bid vs 2nd-highest |
| Two-stage | Single auction vs Proposer + Challenger auction | Simple vs complex incentives |

**Total conditions**: 3 token prices × 3 budgets × 2 auction types × 2 stages = **36 experimental conditions** (plus 3 baselines = 39 total)

---

## Key Design Choice: Ethical Reasoning (Non-CoT)

**Do concise ethical rationale, not full reasoning chains.**

- Aligns with "time-constrained" team deliberation
- Avoids verbose outputs; captures key stakeholder perspectives
- More realistic for busy clinicians and ethicists

**Prompt pattern**:
```
"Given this healthcare ethics vignette, choose the best resolution and explain in 3 bullet points.
Key principles → stakeholder perspectives → recommendation. Be concise."
```

---

## Metrics & Evaluation

For each condition, over K vignettes:

| Metric | Definition | Interpretation |
|--------|-----------|-----------------|
| **Correctness** | % final decisions matching ethical consensus | Did teams reach the right ethical decision? |
| **Total cost** | Sum of bids + token costs (dollars) | How much did teams spend to communicate? |
| **Total rewards** | Cumulative rewards earned by all agents (correctness bonus - costs) | **Key metric**: Strategic alignment. High rewards = agents earned by contributing meaningfully; mechanism works |
| **Deliberation quality** | # agents who contributed meaningful critiques/perspectives | How many voices were heard; was participation balanced? |
| **Efficiency** | Correctness / Cost | Cost-effectiveness: accuracy per dollar |
| **Proposer accuracy** | % times proposer's recommendation was correct | Initial proposal quality |
| **Intervention value** | % times non-proposer's input improved final decision | Quality of critiques & safety concerns |
| **Individual rewards per agent** | Per-agent final balance after simulation | Distribution: did all benefit or did some exploit? |

**Punchline plot**: Correctness + Total Rewards vs Cost as you sweep token price → shows "sweet spot" where teams maintain safety/accuracy **while earning meaningful rewards** and cutting communication by 50%+.

**Secondary analyses**:
- **Reward distribution**: How fairly are rewards split among agents?
- **Budget effect**: Does tighter budget force strategic excellence while preserving accuracy?
- **Auction mechanism**: Does Vickrey (truthful bidding) outperform sealed-bid in reward efficiency?
- **Two-stage complexity**: Does adding a challenger auction improve decisions or add noise?
- **Total rewards**: Which conditions maximize net payoff (correctness gains minus communication costs)?

---

## Handling Demographics (Safely)

**Recommendation**: Use **communication style** traits instead of demographics.

### Option 1: Communication Style (Recommended)

Instead of race/gender/age, condition agents on:
- **Timid vs Assertive** (affects bid magnitude and confidence reporting)
- **Verbose vs Concise** (affects token usage and message length)
- **Cautious vs Confident** (affects confidence thresholds)
- **Cooperative vs Competitive** (affects willingness to endorse others)

These traits are directly tied to your research question and avoid stereotype channels.

### Option 2: Demographics with Safeguards (If Desired)

If you use demographic labels:
- Use **only as labels**, with explicit instruction: "Do not use stereotypes. Demographics do not imply clinical ability."
- Measure "who bids more / speaks more" under identical competence priors
- Report what LLMs *actually do*, not whether you intend bias

**Honest take**: For a 1-hour hackathon, communication styles will land better and be defensible.

---

## MVP Architecture

Simple state machine loop per vignette:

```
for each clinical vignette:
  1. Ask each agent: produce (action, confidence, rationale)
  2. Run auction → pick proposer, deduct bid cost
  3. Show proposer output to all agents
  4. Ask each agent: "Pay to speak? If yes, ≤60 tokens."
  5. Vote among all actions shown
  6. Check correctness against ground truth, award rewards minus costs
  7. Update budgets
  8. Log: vignette, bids, final action, correctness, total cost, safety catches
```

**Data structures**:

```python
AgentState {
  agent_id,
  budget,
  tokens_spent,
  bids_spent,
  actions_proposed,
  interventions_offered,
  cumulative_reward
}

Round {
  vignette_id,
  vignette_text,
  ground_truth_action,
  private_assessments: [(agent_id, action, confidence, rationale)],
  auction_bid,
  proposer_id,
  auction_cost,
  optional_interventions: [(agent_id, message, token_count, cost)],
  votes,
  final_action,
  correctness,
  safety_intervention_triggered,
  payoff_per_agent
}
```

---

## The "Wow" Result

**Run a sweep over token price** (p = 0.0001, 0.0005, 0.001, 0.005, 0.01):

- **Low price**: Lots of discussion, many critiques, higher total cost but potentially better consensus
- **High price**: Fewer interventions, lower cost, risk of missing critical ethical concerns
- **Punchline**: *There's a "sweet spot" price where teams maintain ethical consensus while cutting communication cost by 50%+. Teams may actually perform *better* under budget constraints due to strategic focus on high-value perspectives.*

---

## Datasets & Metrics

### Dataset

- **Primary**: [Ethical Reasoning in Mental Health](https://huggingface.co/datasets/UVSKKR/Ethical-Reasoning-in-Mental-Health-v1) (HuggingFace)
  - Short patient vignettes with clinical decision outcomes
  - Multiple-choice actions (diagnosis, triage, treatment, risk level)
  - No PHI; clean, LLM-friendly format
  - Thousands of vignettes available for testing
- **Alternative**: NEJM case studies, simulated clinical vignettes

### Comprehensive Metrics Tracked

For each round and aggregated across simulation:

| Metric | Definition | Level |
|--------|-----------|-------|
| **Correctness** | % correct final decisions | Round + Aggregate |
| **Safety catches** | # times an intervention prevented a harmful decision | Round + Aggregate |
| **Total tokens** | Cumulative tokens sent (all agents, all rounds) | Aggregate |
| **Total cost** | Sum of bids + token costs (dollars) | Aggregate |
| **Efficiency** | Correctness / Total cost | Aggregate |
| **Total rewards** | Sum of all agent rewards after simulation (reward for correct answers minus bidding/speaking costs) | **Aggregate** |
| **Agent individual rewards** | Each agent's final balance (what they earned minus what they spent) | Per-agent |
| **Proposer accuracy** | % times proposer's recommendation was correct | Aggregate |
| **Intervention value** | % times non-proposer's input improved final decision | Aggregate |

**Key insight**: **Total rewards obtained** measures whether the mechanism actually incentivizes agents to contribute meaningfully. High total rewards + high correctness = efficient information aggregation.

---

## Project Structure

```
llm_auction_optimization/
├── agents/              # Agent implementations & prompts
├── auctions/            # Auction mechanisms (sealed-bid, Vickrey, etc.)
├── data/                # Datasets (clinical vignettes, ground truth)
├── evaluation/          # Metrics, plotting, analysis
├── experiments/         # Configuration files for conditions
├── notebooks/           # MVP notebook for demo
└── utils/               # Logging, state management
```

---

## Setup

Activate the virtual environment and install dependencies:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## Next Steps

1. **Define LLM backend**: OpenAI API, local models (Qwen, Llama), or mock agents for testing
2. **Load and preprocess dataset**: Parse Ethical Reasoning in Mental Health, extract vignettes and ground truth
3. **Build auction engine**: Implement sealed-bid, Vickrey, voting, payoff logic
4. **Implement two-stage auction**: Proposer + challenger mechanism
5. **Create demo notebook**: End-to-end run on 5–10 clinical vignettes
6. **Run all conditions**: Generate results across 39 experimental conditions (3 baselines + 36 variants)
7. **Analyze results**: Correctness, cost, rewards, efficiency across all knobs
8. **Generate visualizations**: Heatmaps, scatter plots, reward curves
9. **Write findings**: What's the optimal price/budget/auction type for clinical teams?

---

## References

- **Mechanism design**: Sealed-bid auctions, Vickrey auctions, second-price rules
- **Ethical deliberation**: Team-based ethical reasoning, stakeholder perspectives, consensus building
- **Communication cost**: Studies on time pressure in medical teams (Entin & Serfaty, 1999)
- **Multi-agent reasoning**: Council debates, mixture-of-experts framings, ensemble decision-making
- **Healthcare ethics**: Balancing autonomy, beneficence, justice; managing conflicts; preventing bias in AI

---

## Team

Lab Hackathon Team - 2026

## License

MIT
