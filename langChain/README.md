# LangChain-Claude CLI Integration

This directory contains examples and utilities for integrating LangChain workflows with Claude CLI using advanced features like session continuity and MCP servers.

## Key Features

### 🔄 Session Continuity
- Use `--continue` to maintain context across multiple interactions
- Preserve todo lists, file states, and conversation history
- Enable complex multi-step workflows

### 🎯 Custom Prompts
- Leverage `-p` option for specialized task modes
- Pre-configured prompts for analysis, implementation, testing
- Context-aware prompt selection

### 🛠️ MCP Integration
- Access to external tools and services
- Database connections, web APIs, file systems
- Extensible tool ecosystem

### 📋 Todo Management
- Synchronize task states between LangChain and Claude
- Track workflow progress
- Automatic state persistence

## Files

- `langchain_claude_integration.py` - Main integration example showing how to use Claude CLI from LangChain agents
- `context_management.md` - Strategies for managing context and state
- `workflow_examples.py` - Common workflow patterns and examples

## Usage Example

```python
from langchain_claude_integration import ClaudeAgent

# Initialize agent with project path
agent = ClaudeAgent("/path/to/your/project")

# Define workflow
workflow = [
    {
        "id": "analyze",
        "type": "analysis", 
        "prompt": "Analyze codebase architecture"
    },
    {
        "id": "implement",
        "type": "implementation",
        "prompt": "Add user authentication"
    }
]

# Execute with session continuity
results = await agent.execute_workflow(workflow)
```

## Integration Benefits

1. **Context Preservation**: Unlike standalone LLM calls, Claude CLI maintains project context
2. **Tool Access**: Direct access to file systems, databases, APIs through MCP
3. **State Management**: Todo lists and checkpoints for complex tasks
4. **Error Recovery**: Session continuity allows resuming interrupted workflows
5. **Performance**: Efficient context reuse reduces token consumption

## Next Steps

- Implement error handling and retry logic
- Add more sophisticated context parsing
- Create workflow templates for common tasks
- Integrate with CI/CD pipelines