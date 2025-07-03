#!/bin/bash
# Final cleanup - remove all build/planning documents

echo "🧹 Cleaning up unnecessary files..."

# Remove all the build planning documents
files_to_remove=(
    "EXECUTION_CHECKLIST.md"
    "EXTRACTION_SUMMARY.md" 
    "FORT_KNOX_STRUCTURE.md"
    "MANUAL_TREE.md"
    "MCP_INFRASTRUCTURE_STATUS.md"
    "MERGE_INSTRUCTIONS.md"
    "NEXT_STEPS.md"
    "PROGRESS_TRACKER.md"
    "STATUS.md"
    "SUMMARY.md"
    "VISUAL_DISTRIBUTION.md"
    "AGENT_ECOSYSTEM_COMPLETE.md"
    "REPOSITORY_COMPLETE.md"
    "REPOSITORY_STRUCTURE_STATUS.md"
    "execute_download.md"
    "download_openwebui.sh"
    "INTEGRATE_OPENWEBUI_FINAL.sh"
    "CLEANUP_LIST.md"
)

for file in "${files_to_remove[@]}"; do
    if [ -f "$file" ]; then
        git rm "$file"
        echo "✅ Removed $file"
    fi
done

echo "📝 Repository is now clean and ready for agents!"
echo "Key files remaining:"
echo "- README.md (AI-first documentation)"
echo "- FILE_TREE.md (Repository structure)"
echo "- Core directories: agents/, openwebui/, fort-knox-apis/, mcp-tools/"

git add -A
git commit -m "Clean up: Remove all build planning documents"
git push
