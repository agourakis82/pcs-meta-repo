#!/usr/bin/env python3
"""
Test script for Phase 1: Validation Infrastructure
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from datasets.validation_utils import run_phase1_validation_infrastructure

if __name__ == "__main__":
    print("🧪 Testing PHASE 1: Validation Infrastructure")
    print("=" * 60)

    # Execute Phase 1
    results = run_phase1_validation_infrastructure()

    print("\n" + "=" * 60)
    print("📋 PHASE 1 TEST RESULTS:")
    print(f"Phase: {results['phase']}")
    print(f"Tasks Completed: {len(results['tasks_completed'])}")
    print(f"Issues Fixed: {len(results['issues_fixed'])}")

    print("\n🎯 Ready for PHASE 2!")
