# Troubleshooting Guide - Common Issues and Solutions

## Session Creation Issues

### Issue: "Session already exists"
```yaml
# Problem session
sessions:
  my-app:
    session_name: "my-app"  # This might already exist
```

**Solution:**
```yaml
sessions:
  my-app:
    session_name: "my-app-${USER}"  # Make it unique per user
    # OR
    force_new: true  # Kill existing session first
```

### Issue: "Directory does not exist"
```yaml
# Problem
start_directory: "/path/that/doesnt/exist"
```

**Solution:**
```yaml
start_directory: "${PROJECT_DIR:-$HOME/projects}"
# OR with auto-creation
before_script: |
  mkdir -p "$START_DIRECTORY"
  cd "$START_DIRECTORY"
```

## Command Execution Issues

### Issue: "Command not found"
```yaml
# Problem
panes:
  - command: "special-tool"  # Tool might not be in PATH
```

**Solution:**
```yaml
panes:
  - command: |
      if command -v special-tool &> /dev/null; then
        special-tool
      else
        echo "special-tool not found. Please install it."
        echo "Installation: brew install special-tool"
      fi
```

### Issue: Commands fail immediately
```yaml
# Problem
panes:
  - command: "npm run dev"  # Might fail if no package.json
```

**Solution:**
```yaml
panes:
  - command: |
      if [ -f "package.json" ]; then
        npm install && npm run dev
      else
        echo "No package.json found"
        bash  # Keep pane open
      fi
```

## Environment Variable Issues

### Issue: Undefined variables
```yaml
# Problem
environment:
  API_URL: "$UNDEFINED_VAR/api"  # Will be empty
```

**Solution:**
```yaml
environment:
  API_URL: "${UNDEFINED_VAR:-http://localhost:8000}/api"
  # OR check in before_script
before_script: |
  if [ -z "$REQUIRED_VAR" ]; then
    echo "Error: REQUIRED_VAR not set"
    exit 1
  fi
```

### Issue: Variable expansion in commands
```yaml
# Problem - variables not expanded
panes:
  - command: 'echo $MY_VAR'  # Single quotes prevent expansion
```

**Solution:**
```yaml
panes:
  - command: "echo $MY_VAR"  # Use double quotes
  # OR
  - command: |
      echo "$MY_VAR"
```

## Pane and Window Issues

### Issue: Panes closing immediately
```yaml
# Problem
panes:
  - command: "echo done"  # Exits immediately
```

**Solution:**
```yaml
panes:
  - command: "echo done; exec bash"  # Keep shell open
  # OR
  - command: |
      echo done
      read -p "Press enter to continue..."
```

### Issue: Layout problems with many panes
```yaml
# Problem
layout: "tiled"
panes: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]  # Too many
```

**Solution:**
```yaml
# Split across multiple windows
windows:
  - window_name: "group1"
    layout: "tiled"
    panes: [1, 2, 3, 4]
  - window_name: "group2"
    layout: "tiled"
    panes: [5, 6, 7, 8]
```

## Permission Issues

### Issue: Permission denied
```yaml
# Problem
start_directory: "/root/protected"
```

**Solution:**
```yaml
start_directory: "${PROTECTED_DIR:-$HOME/fallback}"
# OR
before_script: |
  if [ -w "$START_DIRECTORY" ]; then
    cd "$START_DIRECTORY"
  else
    echo "No write access to $START_DIRECTORY"
    cd "$HOME"
  fi
```

## Performance Issues

### Issue: Resource exhaustion
```yaml
# Problem
panes:
  - command: "while true; do echo 'spam'; done"
```

**Solution:**
```yaml
panes:
  - command: |
      # Add rate limiting
      while true; do
        echo 'controlled output'
        sleep 1
      done
  # OR with resource limits
  - command: |
      ulimit -v 1048576  # 1GB memory limit
      ulimit -t 3600     # 1 hour CPU time
      ./resource-heavy-script.sh
```

## Common Patterns for Robustness

### Conditional execution based on file type
```yaml
panes:
  - command: |
      if [ -f "package.json" ]; then
        npm install && npm run dev
      elif [ -f "requirements.txt" ]; then
        pip install -r requirements.txt && python app.py
      elif [ -f "Gemfile" ]; then
        bundle install && rails server
      elif [ -f "pom.xml" ]; then
        mvn spring-boot:run
      else
        echo "Unknown project type"
        ls -la
      fi
```

### Health checks before starting
```yaml
before_script: |
  # Check required services
  echo "Checking dependencies..."
  
  if ! nc -z localhost 5432; then
    echo "PostgreSQL not running. Starting..."
    brew services start postgresql
    sleep 3
  fi
  
  if ! nc -z localhost 6379; then
    echo "Redis not running. Starting..."
    brew services start redis
    sleep 2
  fi
  
  echo "All services ready!"
```

### Graceful degradation
```yaml
windows:
  - window_name: "main"
    panes:
      - command: |
          # Try optimal setup first
          if command -v claude &> /dev/null; then
            claude --dangerously-skip-permissions
          elif command -v vim &> /dev/null; then
            vim
          else
            # Fallback to basic shell
            echo "No editor found"
            bash
          fi
```

## Debugging Tips

1. **Enable verbose logging:**
   ```yaml
   environment:
     YESMAN_LOG_LEVEL: "debug"
   ```

2. **Test commands individually:**
   ```bash
   # Test your command outside tmux first
   bash -c "your complex command"
   ```

3. **Check tmux session manually:**
   ```bash
   tmux attach -t session-name
   tmux list-sessions
   tmux list-windows -t session-name
   ```

4. **Use echo for debugging:**
   ```yaml
   before_script: |
     echo "Current directory: $(pwd)"
     echo "Environment: $ENVIRONMENT"
     echo "Path: $PATH"
   ```