# Fort Knox Repository Transformation Action Plan

## Current Status Assessment

### ✅ Already Completed
1. **Agent Framework** - Base agent system with 2 working agents
2. **Agent Connector** - FastAPI bridge for Open WebUI integration  
3. **Migration Script** - Ready to reorganize repository structure
4. **Shared Memory** - Communication system for agents
5. **Documentation** - Architecture vision and progress tracking

### 🔄 Ready to Execute
1. **Download Open WebUI** - Script created (`download_openwebui.sh`)
2. **Repository Reorganization** - Script ready (`migrate_repository.sh`)

### ⏳ Remaining Tasks
1. **Open WebUI Integration** - Modify Open WebUI to use agent connector
2. **Complete Agent Implementation** - 3 agents need implementation
3. **Testing & Validation** - Ensure everything works together

## Execution Steps

### Step 1: Download Open WebUI ⏱️ 2-3 minutes
```bash
chmod +x download_openwebui.sh
./download_openwebui.sh
```
This will:
- Clone Open WebUI from GitHub
- Preserve our custom agent_connector.py
- Create integrated README with setup instructions

### Step 2: Reorganize Repository ⏱️ 1-2 minutes  
```bash
chmod +x migrate_repository.sh
./migrate_repository.sh
```
This will:
- Move discovery-docs → fort-knox-apis/
- Move extracted-data → fort-knox-apis/
- Reorganize MCP tools into categories
- Clean up old directories
- Initialize shared memory files

### Step 3: Verify New Structure ⏱️ 1 minute
After migration, the repository should look like:
```
google-mcp-fortknox/
├── /openwebui              # Full Open WebUI source + agent_connector.py
├── /agents                 # 5 agents (2 complete, 3 placeholders)
├── /fort-knox-apis         # All Google API documentation
├── /mcp-tools              # Categorized MCP tools
└── /shared-memory          # Agent communication system
```

### Step 4: Integrate Open WebUI with Agents ⏱️ 10-15 minutes
Modify Open WebUI to:
1. Remove external tool dependencies
2. Add agent discovery UI
3. Connect to agent_connector.py endpoints
4. Enable local-only operation

Key files to modify:
- `openwebui/backend/main.py` - Add agent routes
- `openwebui/src/lib/apis/` - Point to local agents
- `openwebui/src/routes/` - Add agent selection UI

### Step 5: Implement Remaining Agents ⏱️ 20-30 minutes
Complete implementation for:
1. **API Explorer Agent** - Discover and wrap external APIs
2. **Database Admin Agent** - Manage Cloud SQL/Firestore/BigQuery  
3. **Coordinator Agent** - Orchestrate multi-agent tasks

### Step 6: Test End-to-End ⏱️ 10 minutes
1. Start Open WebUI
2. Verify agent discovery
3. Test chat with each agent
4. Test tool creation
5. Test inter-agent communication

## Quick Start Commands

For immediate execution:
```bash
# 1. Download Open WebUI
./download_openwebui.sh

# 2. Reorganize repository
./migrate_repository.sh

# 3. Install dependencies
cd openwebui/backend
pip install -r requirements.txt
cd ../..

# 4. Start the system
cd openwebui
python backend/main.py --agents
```

## Expected Outcome

After completion:
- ✅ Open WebUI provides chat interface to agents
- ✅ Agents can read Fort Knox documentation directly
- ✅ Agents can create MCP tools on demand
- ✅ Agents can spawn other agents
- ✅ Complete autonomous system within single repository

## Time Estimate

- **Automated Tasks**: ~5 minutes (downloading, reorganizing)
- **Integration Tasks**: ~15 minutes (connecting Open WebUI)
- **Implementation Tasks**: ~30 minutes (completing agents)
- **Total**: ~50 minutes for complete transformation

## Risk Mitigation

1. **Backup First**: The migration script moves files, so ensure Git is up to date
2. **Test Locally**: Run in development before production
3. **Incremental Testing**: Test each component as you go
4. **Rollback Plan**: Git reset if needed

## Success Criteria

The transformation is complete when:
1. Open WebUI shows list of available agents
2. User can chat with any agent
3. Agents can create new MCP tools
4. Agents can read Fort Knox documentation
5. System operates without external dependencies