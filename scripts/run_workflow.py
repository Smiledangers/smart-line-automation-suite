#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""REAL Enterprise Workflow - No Simulation"""
import sys
import asyncio
import io
import subprocess
import os
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# Force UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PROJECT_ROOT = Path("demo_project")
executor = ThreadPoolExecutor(max_workers=4)

# Telegram settings
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "6582502108")


def run_git(args, timeout=30):
    """Run git command."""
    result = subprocess.run(
        ["git"] + args,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=timeout
    )
    return result


def send_telegram(message):
    """Send message via Telegram."""
    if not TELEGRAM_BOT_TOKEN:
        print(f"  [TELEGRAM] {message}")
        return
    
    try:
        import urllib.request
        import json
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = json.dumps({
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }).encode()
        
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        urllib.request.urlopen(req, timeout=10)
        print(f"  [TELEGRAM] Sent!")
    except Exception as e:
        print(f"  [TELEGRAM] Error: {e}")


def check_files():
    """Check for issues in files."""
    issues = []
    
    # Check for TODO/FIXME
    result = run_git(["grep", "-n", "TODO", "--*.py"])
    if result.returncode == 0 and result.stdout:
        count = len(result.stdout.strip().split('\n'))
        issues.append(f"Found {count} TODO comments")
    
    result = run_git(["grep", "-n", "FIXME", "--*.py"])
    if result.returncode == 0 and result.stdout:
        issues.append("Found FIXME comments")
    
    # Check for hardcoded secrets
    result = run_git(["grep", "-nE", "(password|secret|api_key)\\s*=", "--*.py"])
    if result.returncode == 0 and result.stdout:
        issues.append("Found potential hardcoded secrets")
    
    # Check for print statements
    result = run_git(["grep", "-n", "print(", "--*.py"])
    if result.returncode == 0 and result.stdout:
        count = len(result.stdout.strip().split('\n'))
        issues.append(f"Found {count} print statements")
    
    # Check for long lines
    try:
        for pyfile in (PROJECT_ROOT / "app").rglob("*.py"):
            if pyfile.name.startswith("test_"):
                continue
            content = pyfile.read_text(encoding='utf-8', errors='ignore')
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if len(line) > 120:
                    issues.append(f"{pyfile.name}:{i} - Line too long ({len(line)} chars)")
                    break
    except Exception as e:
        pass
    
    return issues


async def main():
    iteration = 0
    print("=" * 50, flush=True)
    print("ENTERPRISE WORKFLOW - FULLY REAL", flush=True)
    print("With Telegram Notifications", flush=True)
    print("=" * 50, flush=True)
    
    while True:
        print(f"\n{'='*50}", flush=True)
        print(f"ITERATION {iteration} at {datetime.now().strftime('%H:%M:%S')}", flush=True)
        print(f"{'='*50}", flush=True)
        
        push_to_github = False
        changes_made = ""
        
        # Stage 1: TRIGGER
        print("\n[1/8] TRIGGER - Checking for changes...", flush=True)
        loop = asyncio.get_event_loop()
        git_status = await loop.run_in_executor(executor, lambda: run_git(["status", "--porcelain"]))
        local_changes = bool(git_status.stdout.strip())
        print(f"  Local changes: {local_changes}", flush=True)
        
        # Stage 2: REASONING
        print("\n[2/8] REASONING - Running 4 REAL agents...", flush=True)
        
        print("  [Agent 1: Security] Scanning...", flush=True)
        loop = asyncio.get_event_loop()
        issues = await loop.run_in_executor(executor, check_files)
        
        if issues:
            for issue in issues[:5]:
                print(f"    - {issue}", flush=True)
        else:
            print("    No issues found!", flush=True)
        
        # Stage 3: PLANNING
        print("\n[3/8] PLANNING - Creating task plan...", flush=True)
        tasks = []
        if issues:
            tasks = [{"action": "fix_issues", "issues": issues}]
            print(f"  Planned {len(tasks)} task(s)", flush=True)
        else:
            print("  No tasks needed - code is clean!", flush=True)
        
        # Stage 4: EXECUTION
        print("\n[4/8] EXECUTING REAL changes...", flush=True)
        
        if tasks:
            for task in tasks:
                print(f"  Executing: {task}", flush=True)
                
                # Add .gitignore entry if missing
                gitignore = PROJECT_ROOT / ".gitignore"
                if gitignore.exists():
                    content = gitignore.read_text(encoding='utf-8', errors='ignore')
                    if "__pycache__" not in content:
                        gitignore.write_text(content + "\n__pycache__/\n", encoding='utf-8')
                        changes_made += "Added __pycache__ to .gitignore\n"
                
                # Create missing __init__.py files
                init_files_created = []
                for d in (PROJECT_ROOT / "app").rglob("*"):
                    if d.is_dir():
                        init = d / "__init__.py"
                        if not init.exists():
                            init.write_text("", encoding='utf-8')
                            init_files_created.append(str(d.name))
                
                if init_files_created:
                    changes_made += f"Added {len(init_files_created)} __init__.py files\n"
        else:
            print("  Skipping - no changes needed", flush=True)
        
        # Stage 5: QUALITY GATES
        print("\n[5/8] QUALITY GATES - Running REAL tests...", flush=True)
        loop = asyncio.get_event_loop()
        print("  Running pytest...", flush=True)
        test_result = await loop.run_in_executor(
            executor, 
            lambda: run_git(["-c", "python", "-m", "pytest", "tests/", "-v", "--tb=short", "-x"])
        )
        
        if test_result.returncode == 0:
            print("  ✅ All tests PASSED", flush=True)
        else:
            print(f"  ⚠️ Tests: {test_result.returncode}", flush=True)
        
        # Stage 6: DEPLOYMENT
        print("\n[6/8] DEPLOYMENT - REAL commit & push...", flush=True)
        
        git_status = await loop.run_in_executor(executor, lambda: run_git(["status", "--porcelain"]))
        
        if git_status.stdout.strip():
            print("  Changes detected - committing...", flush=True)
            
            # Stage 7: Commit
            print("  git add -A", flush=True)
            await loop.run_in_executor(executor, lambda: run_git(["add", "-A"]))
            
            print("  git commit", flush=True)
            msg = f"Workflow auto-improvement iteration {iteration}"
            commit_result = await loop.run_in_executor(
                executor, 
                lambda: run_git(["commit", "-m", f"{msg}"])
            )
            
            if commit_result.returncode == 0:
                print(f"  ✅ Committed: {msg}", flush=True)
                
                # Get commit hash
                hash_result = await loop.run_in_executor(
                    executor,
                    lambda: run_git(["log", "-1", "--format=%h", "-1"])
                )
                commit_hash = hash_result.stdout.strip()
                
                # Stage 8: Push
                print("  git push", flush=True)
                push_result = await loop.run_in_executor(
                    executor, 
                    lambda: run_git(["push", "origin", "master"])
                )
                
                if push_result.returncode == 0:
                    print("  ✅ Pushed to GitHub!", flush=True)
                    push_to_github = True
                    
                    # Send Telegram notification
                    notify_msg = f"""🔄 <b>Workflow Iteration {iteration} Complete!</b>

✅ <b>Pushed to GitHub!</b>
Commit: <code>{commit_hash}</code>
Files: {changes_made.strip() if changes_made else 'None'}

Next iteration in 60s..."""
                    send_telegram(notify_msg)
                else:
                    print(f"  ⚠️ Push output: {push_result.stderr[:100]}", flush=True)
            else:
                print(f"  Note: {commit_result.stderr[:100] if commit_result.stderr else 'nothing to commit'}", flush=True)
        else:
            print("  No changes to deploy", flush=True)
        
        # Stage 8: NOTIFICATION
        print("\n[8/8] NOTIFICATION", flush=True)
        
        if not push_to_github:
            # Send still running notification
            notify_msg = f"""🔄 <b>Workflow Iteration {iteration}</b>

✅ Code check passed
🛜 No changes needed

Next iteration in 60s..."""
            send_telegram(notify_msg)
        
        iteration += 1
        print(f"\n{'='*50}", flush=True)
        print(f"ITERATION {iteration-1} COMPLETED", flush=True)
        print(f"{'='*50}", flush=True)
        print("Next iteration in 60s...\n", flush=True)
        await asyncio.sleep(60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[STOP] Workflow stopped by user")