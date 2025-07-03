# Fort Knox Repository Agents
"""
This directory contains all AI agents that live within the repository.
Each agent has direct access to Fort Knox API documentation and can:
- Create new MCP tools
- Spawn other agents
- Communicate via shared memory
- Modify the repository structure
"""

from .base_agent import BaseAgent

__all__ = ['BaseAgent']
