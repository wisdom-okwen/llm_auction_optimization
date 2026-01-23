#!/usr/bin/env python
"""
COMPARATIVE ANALYSIS: Compare baseline results.

This script loads results from free discussion and turn-taking baselines
and generates summary statistics comparing them to the main auction.

Usage:
    python analyze_baselines.py

Output:
    - Console summary table comparing mechanisms
    - Detailed breakdowns by communication style
"""

import os
import sys
import pandas as pd
from pathlib import Path
from collections import defaultdict

def find_latest_runs(data_dir: str = "../../data", mechanisms: list = None) -> dict:
    """Find latest run directories for each mechanism."""
    if mechanisms is None:
        mechanisms = ['auction', 'baseline_free_discussion', 'baseline_turn_taking']
    
    data_path = Path(data_dir)
    runs = {}
    
    for mechanism in mechanisms:
        # Find all runs matching this mechanism
        pattern = f"run_{mechanism}_*"
        matches = sorted(data_path.glob(pattern), reverse=True)
        
        if matches:
            runs[mechanism] = matches[0]
            print(f"✓ Found {mechanism}: {matches[0].name}")
        else:
            print(f"⚠️  No runs found for {mechanism}")
    
    return runs

def load_run_data(run_dir: Path) -> dict:
    """Load all CSV files from a run directory."""
    data = {
        'vignette': None,
        'agent_round': None,
        'agent_summary': None,
        'simulation_summary': None,
    }
    
    try:
        data['vignette'] = pd.read_csv(run_dir / 'vignette_results.csv')
        data['agent_round'] = pd.read_csv(run_dir / 'agent_round_results.csv')
        data['agent_summary'] = pd.read_csv(run_dir / 'agent_summary.csv')
        data['simulation_summary'] = pd.read_csv(run_dir / 'simulation_summary.csv')
    except FileNotFoundError as e:
        print(f"⚠️  Missing file in {run_dir}: {e}")
    
    return data

def analyze_mechanism(name: str, data: dict) -> dict:
    """Analyze results for a single mechanism."""
    if data['agent_round'] is None:
        return None
    
    df = data['agent_round']
    
    # Calculate key metrics
    metrics = {
        'mechanism': name,
        'total_rounds': df['vignette_id'].nunique(),
        'total_agents': df['agent_id'].nunique(),
        'avg_cost': df['total_cost'].mean(),
        'total_cost': df['total_cost'].sum(),
        'avg_reward': df['reward'].mean(),
        'total_reward': df['reward'].sum(),
    }
    
    return metrics

def analyze_by_style(data: dict, mechanism: str) -> pd.DataFrame:
    """Analyze results broken down by communication style."""
    if data['agent_round'] is None:
        return None
    
    df = data['agent_round']
    
    style_results = []
    for style in ['assertive', 'timid', 'calibrated', 'neutral']:
        style_data = df[df['communication_style'] == style]
        
        if len(style_data) > 0:
            style_results.append({
                'mechanism': mechanism,
                'communication_style': style,
                'n_agents': style_data['agent_id'].nunique(),
                'avg_cost': style_data['total_cost'].mean(),
                'avg_reward': style_data['reward'].mean(),
                'total_cost': style_data['total_cost'].sum(),
                'total_reward': style_data['reward'].sum(),
            })
    
    return pd.DataFrame(style_results)

def main():
    print("\n" + "="*70)
    print("BASELINE COMPARISON ANALYSIS")
    print("="*70)
    
    # Find latest runs (baselines in data/baselines, auction in data/)
    print("\n1. Locating latest runs...")
    
    # Look for baselines in data/baselines
    baselines_dir = Path("../../data/baselines")
    auction_dir = Path("../../data")
    
    baseline_runs = {}
    for mechanism in ['free_discussion', 'turn_taking']:
        pattern = f"run_baseline_{mechanism}_*"
        matches = sorted(baselines_dir.glob(pattern), reverse=True)
        if matches:
            baseline_runs[f"baseline_{mechanism}"] = matches[0]
            print(f"✓ Found baseline_{mechanism}: {matches[0].name}")
    
    if len(baseline_runs) < 1:
        print("\n⚠️  No baseline runs found in data/baselines/")
        print("Run: python run_all_baselines.py")
        sys.exit(1)
    
    # Load and analyze each mechanism
    print("\n2. Loading and analyzing data...")
    all_data = {}
    all_metrics = {}
    
    for mechanism, run_dir in baseline_runs.items():
        print(f"\n   {mechanism}:")
        data = load_run_data(run_dir)
        all_data[mechanism] = data
        
        metrics = analyze_mechanism(mechanism, data)
        if metrics:
            all_metrics[mechanism] = metrics
            print(f"     - Rounds: {metrics['total_rounds']}")
            print(f"     - Avg Cost/Agent: ${metrics['avg_cost']:.4f}")
            print(f"     - Avg Reward/Agent: ${metrics['avg_reward']:.4f}")
    
    # Print summary comparison
    print("\n" + "="*70)
    print("SUMMARY COMPARISON")
    print("="*70 + "\n")
    
    if all_metrics:
        comparison_df = pd.DataFrame(all_metrics.values())
        print(comparison_df.to_string(index=False))
    
    # Analyze by communication style
    print("\n" + "="*70)
    print("BREAKDOWN BY COMMUNICATION STYLE")
    print("="*70 + "\n")
    
    all_style_data = []
    for mechanism, data in all_data.items():
        style_df = analyze_by_style(data, mechanism)
        if style_df is not None:
            all_style_data.append(style_df)
    
    if all_style_data:
        combined_style = pd.concat(all_style_data, ignore_index=True)
        print(combined_style.to_string(index=False))
    
    # Summary insights
    print("\n" + "="*70)
    print("KEY INSIGHTS")
    print("="*70 + "\n")
    
    if len(all_metrics) > 0:
        best_reward = max(all_metrics.items(), key=lambda x: x[1]['avg_reward'])
        lowest_cost = min(all_metrics.items(), key=lambda x: x[1]['avg_cost'])
        
        print(f"✓ Best Avg Reward: {best_reward[0]} (${best_reward[1]['avg_reward']:.4f})")
        print(f"✓ Lowest Avg Cost: {lowest_cost[0]} (${lowest_cost[1]['avg_cost']:.4f})")
        
        print("\nImplications:")
        if best_reward[0] != lowest_cost[0]:
            print(f"  - {best_reward[0]} has higher rewards but {lowest_cost[0]} is more efficient")
            print(f"  - Suggests trade-off between effectiveness and cost")
        else:
            print(f"  - {best_reward[0]} dominates in both reward and efficiency")
    
    print(f"\nNext steps:")
    print(f"  1. Compare baselines to main auction in data/")
    print(f"  2. Analyze communication style effects")
    print(f"  3. Run token price sweep (0.0001 to 0.01)")

if __name__ == '__main__':
    main()
