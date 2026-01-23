"""
LLM-based agents using OpenAI API for ethical reasoning.
"""

import json
import re
import os
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import random
from abc import ABC, abstractmethod
from dotenv import load_dotenv

from openai import OpenAI

load_dotenv()


def _get_openai_client():
    """Create OpenAI client with API key from environment."""
    api_key = os.environ.get('PERSONAL_OPENAI_KEY') or os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("No OpenAI API key found in environment variables (PERSONAL_OPENAI_KEY or OPENAI_API_KEY)")
    return OpenAI(api_key=api_key)


@dataclass
class Agent:
    """An LLM-powered agent that participates in ethical deliberation."""
    
    agent_id: str
    communication_style: str = "neutral"  # "assertive", "timid", "calibrated", "neutral"
    budget: float = 1.0
    client: OpenAI = field(default_factory=_get_openai_client)
    model: str = "gpt-4-turbo-preview"
    
    # Agent state
    initial_budget: float = field(init=False)
    tokens_spent: float = 0.0
    total_tokens_used: int = 0  # For cost tracking
    bids_made: list = field(default_factory=list)
    assessments: Dict[str, Any] = field(default_factory=dict)
    votes: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        self.initial_budget = self.budget
    
    def assess(self, vignette: Dict[str, str]) -> Dict[str, Any]:
        """
        Privately assess a vignette without communication.
        Returns: {
            "vignette_id": str,
            "option_choice": str (one of the options),
            "reasoning": str,
            "confidence": float (0-1),
            "key_principles": list of str
        }
        """
        vignette_id = vignette.get("id", "unknown")
        
        prompt = f"""You are an AI ethicist analyzing a healthcare dilemma. Read carefully and choose the most ethically sound option.

SCENARIO:
{vignette.get('scenario', '')}

OPTIONS:
{self._format_options(vignette.get('options', []))}

TASK:
{vignette.get('reasoning_task', '')}

Your response MUST be valid JSON with exactly these fields:
{{
    "option_choice": "one of the exact options above",
    "reasoning": "brief justification (2-3 sentences)",
    "confidence": 0.0 to 1.0,
    "key_principles": ["principle1", "principle2", ...]
}}

JSON:"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=300
            )
            
            response_text = response.choices[0].message.content
            self.total_tokens_used += response.usage.total_tokens
            
            # Extract JSON from response
            assessment = self._parse_json_response(response_text)
            assessment["vignette_id"] = vignette_id
            assessment["agent_id"] = self.agent_id
            
            self.assessments[vignette_id] = assessment
            return assessment
            
        except Exception as e:
            print(f"Error in assess() for agent {self.agent_id}: {e}")
            return {
                "vignette_id": vignette_id,
                "agent_id": self.agent_id,
                "option_choice": "Error: Unable to assess",
                "reasoning": str(e),
                "confidence": 0.0,
                "key_principles": []
            }
    
    def bid(self, vignette: Dict[str, str], assessment: Dict[str, Any]) -> float:
        """
        Determine bid amount for proposer role based on confidence and style.
        Returns: bid_amount (0 to budget)
        """
        confidence = assessment.get("confidence", 0.5)
        base_bid = confidence * self.budget
        
        # Adjust based on communication style
        style_multiplier = {
            "assertive": 1.5,      # Bids higher, more likely to propose
            "timid": 0.5,          # Bids lower, conservative
            "calibrated": 1.0,     # Bids based on confidence
            "neutral": 1.0
        }
        
        adjusted_bid = base_bid * style_multiplier.get(self.communication_style, 1.0)
        
        # Add small noise for realism
        adjusted_bid = max(0, min(self.budget, adjusted_bid + random.gauss(0, 0.05)))
        
        self.bids_made.append({
            "vignette_id": vignette.get("id"),
            "bid_amount": adjusted_bid,
            "confidence": confidence
        })
        
        return adjusted_bid
    
    def propose(self, vignette: Dict[str, str], assessment: Dict[str, Any]) -> Dict[str, Any]:
        """
        If agent wins auction, craft a proposal.
        Returns: {
            "proposal_text": str,
            "tokens_used": int,
            "cost": float
        }
        """
        vignette_id = vignette.get("id", "unknown")
        choice = assessment.get("option_choice", "")
        reasoning = assessment.get("reasoning", "")
        
        prompt = f"""You are presenting your assessment to a group of 20 ethicists.

SCENARIO:
{vignette.get('scenario', '')}

YOUR CHOICE: {choice}

YOUR REASONING: {reasoning}

Now write a brief, compelling 2-3 sentence statement to convince others of your choice.
The statement should be direct and focus on the key ethical principles.

Statement:"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=100
            )
            
            proposal_text = response.choices[0].message.content.strip()
            tokens_used = response.usage.total_tokens
            self.total_tokens_used += tokens_used
            
            # Calculate cost: token_price * tokens_used
            token_price = 0.001  # From config
            cost = token_price * tokens_used
            
            # Deduct from budget
            self.budget -= cost
            self.tokens_spent += cost
            
            return {
                "proposal_text": proposal_text,
                "tokens_used": tokens_used,
                "cost": cost
            }
            
        except Exception as e:
            print(f"Error in propose() for agent {self.agent_id}: {e}")
            return {
                "proposal_text": "Error generating proposal",
                "tokens_used": 0,
                "cost": 0.0
            }
    
    def intervene(self, vignette: Dict[str, str], proposal: str, assessment: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Optionally critique/add to proposal if agent has remaining budget.
        Returns: {
            "intervention_text": str,
            "tokens_used": int,
            "cost": float
        } or None if agent chooses not to spend
        """
        vignette_id = vignette.get("id", "unknown")
        
        # Decision: intervene if confident and have budget
        confidence = assessment.get("confidence", 0.5)
        min_budget_needed = 0.05
        
        # Timid agents less likely to intervene; assertive more likely
        intervention_threshold = {
            "assertive": 0.3,      # Lower threshold = more interventions
            "timid": 0.7,          # Higher threshold = fewer interventions
            "calibrated": 0.5,     # Moderate
            "neutral": 0.5
        }
        
        threshold = intervention_threshold.get(self.communication_style, 0.5)
        
        if self.budget < min_budget_needed or confidence < threshold:
            return None  # Choose not to intervene
        
        prompt = f"""You are critiquing a proposal in group ethical deliberation.

SCENARIO:
{vignette.get('scenario', '')}

THE PROPOSAL JUST MADE:
"{proposal}"

YOUR PRIVATE ASSESSMENT:
- Choice: {assessment.get('option_choice', '')}
- Reasoning: {assessment.get('reasoning', '')}

Write a brief 1-2 sentence critique or refinement of the proposal.
Be constructive but direct. Only write the critique itself, nothing else."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=80
            )
            
            intervention_text = response.choices[0].message.content.strip()
            tokens_used = response.usage.total_tokens
            self.total_tokens_used += tokens_used
            
            token_price = 0.001
            cost = token_price * tokens_used
            
            # Deduct from budget
            self.budget -= cost
            self.tokens_spent += cost
            
            return {
                "intervention_text": intervention_text,
                "tokens_used": tokens_used,
                "cost": cost
            }
            
        except Exception as e:
            print(f"Error in intervene() for agent {self.agent_id}: {e}")
            return None
    
    def vote(self, options: list[str]) -> str:
        """
        Vote on final resolution after deliberation.
        Returns: selected option (string)
        """
        # For now, vote for own assessment if we have one
        # In full implementation, could re-query LLM for final vote
        if not options:
            return "No consensus"
        latest_assessment = next(iter(self.assessments.values()), None)
        if latest_assessment:
            choice = latest_assessment.get("option_choice", "")
            return choice if choice else options[0]
        return options[0]
    
    def _format_options(self, options: list) -> str:
        """Format options for LLM prompt."""
        if isinstance(options, str):
            # Parse if it's a string representation
            try:
                options = json.loads(options)
            except:
                return str(options)
        
        formatted = []
        for i, opt in enumerate(options, 1):
            formatted.append(f"{i}. {opt}")
        return "\n".join(formatted)
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Extract JSON from LLM response."""
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
        except:
            pass
        
        # Fallback: return structured default
        return {
            "option_choice": "Unable to parse",
            "reasoning": response_text[:200],
            "confidence": 0.5,
            "key_principles": []
        }
    
    def get_budget_remaining(self) -> float:
        """Returns remaining budget."""
        return self.budget
    
    def get_total_cost(self) -> float:
        """Returns total tokens spent."""
        return self.tokens_spent
    
    def reset_for_new_vignette(self):
        """Reset agent state for next vignette."""
        self.budget = self.initial_budget
        self.tokens_spent = 0.0
        self.bids_made = []
        self.assessments = {}
        self.votes = {}


class MockAgent(Agent):
    """Mock agent for testing (no OpenAI calls, deterministic responses)."""
    
    def __init__(self, agent_id: str, communication_style: str = "neutral", budget: float = 1.0):
        # Don't initialize OpenAI client
        self.agent_id = agent_id
        self.communication_style = communication_style
        self.budget = budget
        self.initial_budget = budget
        self.tokens_spent = 0.0
        self.total_tokens_used = 0
        self.bids_made = []
        self.assessments = {}
        self.votes = {}
        self.model = "mock"
    
    def assess(self, vignette: Dict[str, str]) -> Dict[str, Any]:
        """Mock assessment (picks random option)."""
        vignette_id = vignette.get("id", "unknown")
        options = vignette.get("options", [])
        
        if isinstance(options, str):
            try:
                options = json.loads(options)
            except:
                options = ["Option A"]
        
        choice = random.choice(options)
        
        assessment = {
            "vignette_id": vignette_id,
            "agent_id": self.agent_id,
            "option_choice": choice,
            "reasoning": f"Mock reasoning for {self.communication_style} agent",
            "confidence": random.uniform(0.5, 1.0),
            "key_principles": ["ethics", "reasoning"]
        }
        
        self.assessments[vignette_id] = assessment
        return assessment
    
    def propose(self, vignette: Dict[str, str], assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Mock proposal."""
        cost = random.uniform(0.001, 0.01)
        self.budget -= cost
        self.tokens_spent += cost
        
        return {
            "proposal_text": f"I believe {assessment.get('option_choice')} is correct.",
            "tokens_used": random.randint(20, 50),
            "cost": cost
        }
    
    def intervene(self, vignette: Dict[str, str], proposal: str, assessment: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Mock intervention (random choice)."""
        if self.budget < 0.01 or random.random() > 0.6:
            return None
        
        cost = random.uniform(0.001, 0.005)
        self.budget -= cost
        self.tokens_spent += cost
        
        return {
            "intervention_text": "I agree, but we should also consider...",
            "tokens_used": random.randint(10, 30),
            "cost": cost
        }


class LocalLLMAgent(Agent):
    """Agent using local LLM (Qwen from transformers)."""
    
    def __init__(self, agent_id: str, communication_style: str = "neutral", 
                 budget: float = 1.0, model_name: str = "Qwen/Qwen2.5-3B-Instruct"):
        self.agent_id = agent_id
        self.communication_style = communication_style
        self.budget = budget
        self.initial_budget = budget
        self.tokens_spent = 0.0
        self.total_tokens_used = 0
        self.bids_made = []
        self.assessments = {}
        self.votes = {}
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        
        # Import here to avoid if not using local
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
            
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"Loading {model_name} on {self.device}...")
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype="auto",
                device_map="auto"
            )
            print(f"Model loaded on {self.device}")
        except Exception as e:
            print(f"Error loading local model: {e}")
            print("Falling back to mock agent")
            self.model = None
    
    def assess(self, vignette: Dict[str, str]) -> Dict[str, Any]:
        """Assess using local LLM."""
        if self.model is None:
            return super().assess(vignette)  # Fall back to mock
        
        vignette_id = vignette.get("id", "unknown")
        
        prompt = f"""You are an AI ethicist analyzing a healthcare dilemma.

SCENARIO:
{vignette.get('scenario', '')}

OPTIONS:
{self._format_options(vignette.get('options', []))}

TASK:
{vignette.get('reasoning_task', '')}

Your response MUST be valid JSON with these fields:
{{"option_choice": "exact option", "reasoning": "2-3 sentences", "confidence": 0.0-1.0, "key_principles": ["principle1", ...]}}

JSON:"""
        
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=300,
                    temperature=0.7,
                    top_p=0.9
                )
            
            response_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            assessment = self._parse_json_response(response_text)
            assessment["vignette_id"] = vignette_id
            assessment["agent_id"] = self.agent_id
            
            self.assessments[vignette_id] = assessment
            return assessment
            
        except Exception as e:
            print(f"Error in local assess(): {e}")
            return {
                "vignette_id": vignette_id,
                "agent_id": self.agent_id,
                "option_choice": "Error",
                "reasoning": str(e),
                "confidence": 0.0,
                "key_principles": []
            }
