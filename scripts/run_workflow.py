#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Start the continuous workflow engine.
"""
import asyncio
import sys
import os
import io

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.workflow.engine import workflow_engine


async def main():
    """Start the workflow engine and run indefinitely."""
    print("===========================================")
    print("  STARTING ENTERPRISE WORKFLOW ENGINE")
    print("===========================================")
    print("  Workflow: Trigger -> Reasoning -> Planning -> Execution -> QA -> Deploy -> Monitor -> Notify")
    print("  Mode: Continuous Loop")
    print("===========================================")
    
    # Start the engine
    await workflow_engine.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[STOP] Workflow engine stopped")
        exit(0)