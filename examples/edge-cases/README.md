# Edge Cases and Error Handling Examples

This directory contains examples of edge cases, error scenarios, and their solutions.

## Files in this Directory

### Configuration Files
- `projects.yaml` - Various edge case scenarios in session configuration
- `error-scenarios.yaml` - Additional error handling examples
- `yesman.yaml` - Edge cases in main configuration

### Documentation
- `troubleshooting-guide.md` - Comprehensive troubleshooting guide with solutions

## Common Edge Cases Covered

### 1. Session Name Issues
- Very long session names
- Special characters in names
- Duplicate session names
- Unicode in session names

### 2. Directory and Path Issues
- Non-existent directories
- Permission denied scenarios
- Relative vs absolute paths
- Environment variable expansion

### 3. Command Failures
- Missing executables
- Commands that exit immediately
- Resource-intensive commands
- Network-dependent commands

### 4. Environment Variables
- Undefined variables
- Circular references
- Multi-line values
- Special characters

### 5. Template and Inheritance
- Missing templates
- Circular dependencies
- Override conflicts
- Deep merging issues

### 6. Resource Management
- Memory limits
- CPU throttling
- Fork bomb protection
- File descriptor limits

### 7. Timing and Synchronization
- Race conditions between panes
- Dependent service startup
- Health check requirements
- Retry logic

### 8. Signal Handling
- Graceful shutdown
- Cleanup on exit
- Signal trapping
- Process management

## Best Practices for Error Handling

### 1. Always Provide Fallbacks
```yaml
start_directory: "${PROJECT_DIR:-$HOME}"
template_name: "custom-template"
fallback_template: "default"
```

### 2. Check Before Executing
```yaml
before_script: |
  # Check prerequisites
  if ! command -v required-tool &> /dev/null; then
    echo "Error: required-tool not installed"
    exit 1
  fi
```

### 3. Use Conditional Logic
```yaml
panes:
  - command: |
      if [ -f "config.json" ]; then
        ./start-with-config.sh
      else
        ./start-with-defaults.sh
      fi
```

### 4. Handle Failures Gracefully
```yaml
panes:
  - command: "risky-command || echo 'Command failed, continuing...'"
    restart_on_exit: true
    max_restarts: 3
```

### 5. Provide Clear Error Messages
```yaml
before_script: |
  if [ -z "$API_KEY" ]; then
    echo "ERROR: API_KEY environment variable is required"
    echo "Please set: export API_KEY=your-key"
    exit 1
  fi
```

## Testing Edge Cases

To test these edge cases:

1. Copy the example configuration
2. Modify for your specific scenario
3. Run with debug logging:
   ```bash
   YESMAN_LOG_LEVEL=debug yesman up
   ```

4. Check tmux session:
   ```bash
   tmux attach -t session-name
   ```

## Contributing

If you encounter new edge cases:

1. Document the issue
2. Create a minimal reproducible example
3. Add the solution to this directory
4. Update the troubleshooting guide

## See Also

- [Configuration Hierarchy](../configuration-hierarchy/)
- [Advanced Examples](../advanced/)
- [Team Collaboration](../team-collaboration/)