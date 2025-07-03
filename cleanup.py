#!/usr/bin/env python3
"""
Final cleanup script to remove all unnecessary build/planning files
Run this locally to clean up the repository
"""

import subprocess
import os

files_to_remove = [
    "EXTRACTION_SUMMARY.md",
    "FORT_KNOX_STRUCTURE.md", 
    "MANUAL_TREE.md",
    "MCP_INFRASTRUCTURE_STATUS.md",
    "MERGE_INSTRUCTIONS.md",
    "NEXT_STEPS.md",
    "PROGRESS_TRACKER.md",
    "STATUS.md",
    "SUMMARY.md",
    "VISUAL_DISTRIBUTION.md",
    "AGENT_ECOSYSTEM_COMPLETE.md",
    "REPOSITORY_COMPLETE.md",
    "REPOSITORY_STRUCTURE_STATUS.md",
    "execute_download.md",
    "download_openwebui.sh",
    "INTEGRATE_OPENWEBUI_FINAL.sh",
    "CLEANUP_LIST.md",
    "cleanup_final.sh"  # Remove this script too after running
]

print("🧹 Starting repository cleanup...")

for file in files_to_remove:
    if os.path.exists(file):
        try:
            subprocess.run(["git", "rm", file], check=True)
            print(f"✅ Removed {file}")
        except:
            print(f"❌ Failed to remove {file}")
    else:
        print(f"⏭️  {file} already removed")

print("\n📝 Committing changes...")
subprocess.run(["git", "add", "-A"])
subprocess.run(["git", "commit", "-m", "Clean up: Remove all build planning and status documents"])

print("\n✨ Repository is now clean!")
print("\nRemaining structure:")
print("- Core directories: agents/, openwebui/, fort-knox-apis/, mcp-tools/")
print("- Essential files: README.md, FILE_TREE.md, test_agents.py")
print("- Deployment files: deploy.sh, cloudbuild.yaml")
