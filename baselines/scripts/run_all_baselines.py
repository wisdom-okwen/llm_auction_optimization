#!/usr/bin/env python
"""
Run ALL BASELINE MECHANISMS and compare results.
"""

import os
import sys
import subprocess
import pandas as pd
from datetime import datetime

def run_mechanism(script_name, mechanism_name):
    """Run a baseline mechanism script."""
    print(f"\n{'='*70}")
    print(f"Running: {mechanism_name}")
    print(f"{'='*70}")
    
    result = subprocess.run(
        [sys.executable, script_name],
        cwd=os.path.dirname(__file__),
        capture_output=False
    )
    
    if result.returncode != 0:
        print(f"⚠️  {mechanism_name} simulation failed!")
        return None
    
    print(f"✓ {mechanism_name} simulation complete!")
    return True

def main():
    print("\n" + "="*70)
    print("BASELINE COMPARISON: All Baselines")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    mechanisms = [
        ('run_free_discussion.py', 'Free Discussion'),
        ('run_turn_taking.py', 'Turn-Taking'),
    ]
    
    results = {}
    for script, name in mechanisms:
        if run_mechanism(script, name):
            results[name] = 'completed'
        else:
            results[name] = 'failed'
    
    print("\n" + "="*70)
    print("COMPARISON SUMMARY")
    print("="*70)
    
    for mechanism, status in results.items():
        symbol = "✓" if status == "completed" else "✗"
        print(f"{symbol} {mechanism}: {status}")
    
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nNext steps:")
    print("1. Compare CSV outputs in data/baselines/ directories")
    print("2. Run: python analyze_baselines.py")
    print("3. Compare against main auction in data/")
    
if __name__ == '__main__':
    main()
