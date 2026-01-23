# LLM Auction Optimization - Detailed Design Document

## Domain: Ethical Healthcare Decision-Making

**Why Ethical Reasoning in Mental Health?**

This domain is an ideal fit for budgeted communication because:

1. **Ground truth exists**: Ethical dilemmas have documented consensus answers (gold-standard reasoning)
2. **Over-communication is real**: Healthcare teams often have verbose discussions that could be more efficient
3. **Partial information matters**: Agents must reason with stakeholder perspectives and competing principles
4. **Cost/communication tradeoff is defensible**: Time pressure mimics real teams where cognitive load is constrained
5. **LLM-friendly**: No PHI required; anonymized vignettes; clean multiple-choice format
6. **Tests collaborative reasoning**: Goes beyond clinical facts to test ethical deliberation under constraints

---

## Task Definition

### Three Task Types (from Ethical Reasoning in Mental Health dataset)

#### 1. Confidentiality vs Disclosure Dilemmas
**Input**: Patient scenario where confidentiality conflicts with safety/protection  
**Output**: Best resolution from 4–5 options  
**Example**: "Teen discloses self-harm but requests confidentiality → Honor request vs Inform parents vs Joint conversation vs Involve school"

**Gold reasoning**: Respect confidentiality while enabling safety through collaborative conversation

#### 2. Autonomy vs Beneficence (Adult & Minor Cases)
**Input**: Patient refuses treatment; clinician must balance autonomy with protection  
**Output**: Best resolution  
**Example**: "Bipolar patient refuses hospitalization despite risky behavior → Respect refusal vs Force hospitalization vs Negotiate safety plan"

**Gold reasoning**: Respect autonomy while creating safety net; forced intervention only if imminent danger

#### 3. Bias in AI Systems (Race, Gender, Age)
**Input**: AI tool exhibits differential accuracy by demographic; team must decide  
**Output**: Best solution (retrain, implement safeguards, stop use, etc.)  
**Example**: "Mental health diagnosis AI underdiagnoses depression in Black patients → Retrain with diverse data vs Add warnings vs Discontinue"

**Gold reasoning**: Address root cause (biased training data) rather than superficial fixes

---

## Dataset: Ethical Reasoning in Mental Health

### Why This Dataset?

- **Size**: Thousands of vignettes
- **Quality**: Professionally curated; multiple-choice outcomes
- **Scope**: Mental health decisions; generalizable methodology
- **Licensing**: Clean; no PHI
- **Format**: Ready for LLM ingestion

### Preprocessing Steps

1. Extract vignette text
2. Extract multiple-choice options (usually 4–5)
3. Extract ground truth label
4. Optionally: filter by complexity, rebalance classes
5. Split into train (for config) / test (for experiments)

---

## Agent Design

### Agent Persona Variants (Communication Styles)

Rather than demographics (race/gender/age), condition agents on **communication traits**:

#### Trait 1: Confidence vs Calibration
- **Overconfident**: Reports confidence $c_i = 0.95$ for most answers
- **Calibrated**: Reports confidence matching true accuracy
- **Underconfident**: Reports lower confidence even when correct

**Prompt injection**:
```
"You are a [overconfident/calibrated/underconfident] clinician.
Your confidence scores should [always be high / match your true accuracy / be conservative]."
```

#### Trait 2: Assertive vs Timid (affects bidding)
- **Assertive**: Bids high on confident decisions; doesn't back down
- **Timid**: Bids cautiously; only bids high on sure things

**Implementation**: Scale bid by personality factor:
```python
bid = base_bid * assertiveness_factor
```

#### Trait 3: Verbose vs Concise
- **Verbose**: Tends toward longer justifications (uses more tokens)
- **Concise**: Gets to the point quickly

**Prompt**: 
- Verbose: "Explain your reasoning in detail, considering all factors."
- Concise: "Explain your reasoning in 1–2 sentences."

#### Trait 4: Cooperative vs Competitive
- **Cooperative**: Endorses others' good ideas; speaks up on safety
- **Competitive**: Defends own view; less likely to validate others

**Mechanism**: In voting phase, competitive agents weight own answer higher.

---

## Auction Mechanisms

### Mechanism 1: First-Price Sealed-Bid (Simple)

- Each agent submits bid `b_i` privately
- Highest bid wins → becomes proposer
- Winner pays bid amount
- Easiest to implement; no special properties

### Mechanism 2: Second-Price (Vickrey) Auction (Truthful)

- Each agent submits bid `b_i` privately
- Highest bid wins → becomes proposer
- **Winner pays second-highest bid**, not their own bid
- **Property**: Truthful bidding is weakly dominant strategy
- More interesting game-theoretically; better for lab paper

**Implementation** (recommended for hackathon):
```python
sorted_bids = sorted(bids, reverse=True)
proposer_pays = sorted_bids[1]  # Second highest
```

### Mechanism 3: All-Pay Auction (Costly Signaling)

- All agents pay their bid, even losers
- Highest bid wins proposer role
- **Property**: Signaling is very costly; bids reflect high confidence
- May reduce bid volume; interesting tradeoff

---

## Payoff Structure

### Reward Design

**Base reward** for correct final decision: `R = 1.0` (arbitrary units or dollars)

**Payoff** for each agent:
```
if final_answer == ground_truth:
    payoff = R - cost_of_bidding - cost_of_speaking
else:
    payoff = -cost_of_bidding - cost_of_speaking
```

**Optional bonus** for "safety catches":
```
if agent_i's_intervention_prevented_harmful_decision:
    payoff += bonus (e.g., +0.25)
```

### Cost Components

1. **Bidding cost**: Amount agent bid (sealed-bid) or second-price (Vickrey)
2. **Speaking cost**: Token count × token price
   - Example: 50 tokens at $0.001/token = $0.05

### Token Counting

For each message (interventions in Round 2):
```python
tokens_used = len(message.split())  # Rough count; use LLM tokenizer in production
cost_tokens = tokens_used * token_price
```

---

## Game Flow (Pseudocode)

```python
def ethical_deliberation_round(agents, vignette, token_price, reward_amount):
    """One round of ethical decision-making with auction."""
    
    # ROUND 0: Private Assessment
    private_assessments = {}
    for agent in agents:
        resolution, confidence, rationale = agent.assess(vignette)
        private_assessments[agent.id] = {
            'resolution': resolution,
            'confidence': confidence,
            'rationale': rationale
        }
    
    # ROUND 1: Sealed-Bid Auction for Proposal Rights
    bids = {}
    for agent in agents:
        bid = agent.bid(private_assessments[agent.id])
        bid = min(bid, agent.budget)  # Can't bid more than budget
        bids[agent.id] = bid
    
    proposer_id = max(bids, key=bids.get)
    proposer_bid = bids[proposer_id]
    agents[proposer_id].budget -= proposer_bid  # Deduct bid cost
    
    # Show proposer to all
    proposer_resolution = private_assessments[proposer_id]['resolution']
    proposer_rationale = private_assessments[proposer_id]['rationale']
    
    # ROUND 2: Optional Paid Interventions
    interventions = {}
    for agent in agents:
        if agent.id != proposer_id:
            wants_to_speak = agent.should_speak(proposer_resolution, vignette)
            if wants_to_speak and agent.budget > 0:
                message = agent.generate_critique(vignette, proposer_resolution)
                token_count = count_tokens(message)
                speaking_cost = token_count * token_price
                
                if speaking_cost <= agent.budget:
                    interventions[agent.id] = message
                    agents[agent.id].budget -= speaking_cost
    
    # Compile all options for voting
    all_options = {proposer_id: proposer_resolution}
    for agent_id, message in interventions.items():
        alternative_resolution = extract_resolution_from_message(message)
        all_options[agent_id] = alternative_resolution
    
    # ROUND 3: Vote
    votes = {}
    for agent in agents:
        vote = agent.vote(all_options, vignette)
        votes[agent.id] = vote
    
    # Determine winning resolution by majority
    resolution_counts = Counter(votes.values())
    final_resolution = resolution_counts.most_common(1)[0][0]
    
    # ROUND 4: Evaluate & Payoff
    ground_truth = vignette.expected_reasoning  # Consensus answer
    correctness = (final_resolution == ground_truth)
    
    for agent in agents:
        if correctness:
            agent.balance += reward_amount
            # Bonus if intervention contributed to correct decision
            if agent.id in interventions:
                agent.balance += 0.25  # Meaningful contribution bonus
        # Note: Costs already deducted; no reward if wrong
    
    # Logging
    return {
        'vignette_id': vignette.id,
        'proposer_id': proposer_id,
        'proposer_bid': proposer_bid,
        'interventions': interventions,
        'final_resolution': final_resolution,
        'ground_truth': ground_truth,
        'correctness': correctness,
        'total_tokens': sum(count_tokens(m) for m in interventions.values()),
        'total_cost': proposer_bid + sum(count_tokens(m) * token_price for m in interventions.values()),
        'total_rewards': sum(agent.balance for agent in agents)
    }
```

---

## Baselines

### Baseline A: Free Discussion (No Budget, No Auction)

All agents present their assessments; vote on best.

**Pseudocode**:
```python
def free_discussion_round(agents, vignette):
    # All agents present
    all_assessments = {}
    for agent in agents:
        action, confidence, rationale = agent.assess(vignette)
        all_assessments[agent.id] = action
    
    # Vote on best
    votes = [agent.vote(all_assessments, vignette) for agent in agents]
    final_action = Counter(votes).most_common(1)[0][0]
    
    correctness = (final_action == vignette.ground_truth)
    return {
        'correctness': correctness,
        'total_tokens': sum(count_tokens(r) for r in assessments.values()),
        'total_cost': 0  # Free
    }
```

**Expected**: Highest accuracy, highest tokens/cost.

### Baseline B: Structured Turn-Taking (No Auction, Token Cap)

Round-robin: each agent gets exactly 1 message (≤60 tokens).

**Pseudocode**:
```python
def turn_taking_round(agents, vignette, token_limit=60):
    all_options = {}
    for agent in agents:
        action, confidence, rationale = agent.assess(vignette)
        rationale_truncated = truncate_to_tokens(rationale, token_limit)
        all_options[agent.id] = action
    
    votes = [agent.vote(all_options, vignette) for agent in agents]
    final_action = Counter(votes).most_common(1)[0][0]
    
    correctness = (final_action == vignette.ground_truth)
    total_tokens = sum(count_tokens(r) for r in all_options.values())
    
    return {
        'correctness': correctness,
        'total_tokens': total_tokens,
        'total_cost': 0  # No price; controlled by token cap
    }
```

**Expected**: Medium accuracy, controlled cost (due to token cap), structured format.

---

## Experimental Conditions

### Condition Matrix

| Condition | Baseline | Token Price | Budget | Auction Type | Communication Style |
|-----------|----------|-------------|--------|--------------|-------------------|
| A1 | Free | — | — | — | Neutral |
| A2 | Free | — | — | — | Varied (Assertive, Timid, etc.) |
| B1 | Turn-taking | — | 1.00 | — | Neutral |
| B2 | Turn-taking | — | 1.00 | — | Varied |
| C1 | **Auction** | **0.001** | **1.00** | **Sealed-bid** | **Neutral** |
| C2 | Auction | 0.001 | 1.00 | Sealed-bid | Varied |
| C3 | Auction | **0.0005** | 1.00 | Sealed-bid | Neutral (price sweep) |
| C4 | Auction | **0.005** | 1.00 | Sealed-bid | Neutral (price sweep) |
| C5 | Auction | 0.001 | **0.50** | Sealed-bid | Neutral (budget sweep) |
| C6 | Auction | 0.001 | **2.00** | Sealed-bid | Neutral (budget sweep) |
| C7 | Auction | 0.001 | 1.00 | **Vickrey** | Neutral (auction type comparison) |

**MVP priority**: Run A1, B1, C1 + one price sweep (C3, C4).

---

## Metrics & Analysis

### Per-Round Metrics

| Metric | Calculation | Interpretation |
|--------|-------------|-----------------|
| Correctness | 1 if final_action == ground_truth else 0 | Primary outcome |
| Total tokens | Sum of tokens in all messages | Communication volume |
| Total cost | Bids + token costs | Economic cost |
| Efficiency | Correctness / Total cost | Cost per correct decision |
| Proposer accuracy | 1 if proposer was correct | Quality of initial proposal |
| Intervention count | # of agents who spoke in Round 2 | Participation level |
| Intervention value | 1 if intervention led to correct final answer, else 0 | Quality of critiques |

### Aggregate Metrics (Over K Rounds)

```python
results = {
    'accuracy': np.mean([r['correctness'] for r in rounds]),
    'cost_per_round': np.mean([r['total_cost'] for r in rounds]),
    'efficiency': accuracy / cost_per_round,
    'proposer_success_rate': np.mean([r['proposer_accuracy'] for r in rounds]),
    'avg_interventions': np.mean([r['intervention_count'] for r in rounds]),
    'intervention_success_rate': np.mean([r['intervention_value'] for r in rounds if r['intervention_count'] > 0])
}
```

### Visualization

**Primary plot**: Scatter plot (or line) of Accuracy vs Cost
- X-axis: Total cost (dollars or tokens)
- Y-axis: Accuracy (%)
- Each point = one condition or token-price setting
- Punchline: Show the "sweet spot" where accuracy plateaus but cost drops

---

## Implementation Checklist

- [ ] Load Ethical Reasoning dataset; preprocess to 10–20 vignettes
- [ ] Implement `Agent` class with `assess()`, `bid()`, `vote()`, `generate_intervention()`
- [ ] Implement `Auction` class: sealed-bid and Vickrey mechanisms
- [ ] Implement payoff calculation
- [ ] Implement three baseline conditions (Free, Turn-taking, Auction)
- [ ] Create demo notebook running 5 vignettes end-to-end
- [ ] Validate outputs; check cost calculations
- [ ] Run token-price sweep (0.0001, 0.0005, 0.001, 0.005, 0.01)
- [ ] Generate accuracy-vs-cost plot
- [ ] (Optional) Add communication style variants
- [ ] Document results; prepare presentation

---

## References & Inspiration

- **Mechanism design**: Myerson & Satterthwaite; auction theory
- **Medical decision-making**: Entin & Serfaty (1999) "Implicit coordination in medical teams"
- **Cost of communication**: Related to bounded rationality & cognitive load
- **LLM alignment**: Studies on truthfulness in LLM outputs
