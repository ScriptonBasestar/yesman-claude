# Complete Project Example

This example demonstrates a complete, production-ready project setup using yesman-claude.

## Project Structure

```
my-saas-app/
├── .yesman/                  # Project-specific yesman config
│   ├── yesman.yaml          # Local overrides
│   └── projects.yaml        # Project sessions
├── frontend/                # React frontend
├── backend/                 # FastAPI backend
├── mobile/                  # React Native app
├── infrastructure/          # Docker, K8s configs
├── docs/                    # Documentation
└── scripts/                 # Utility scripts
```

## Configuration Files

### `.yesman/yesman.yaml`
```yaml
# Project-specific settings
log_level: debug
log_path: ./logs/yesman/

# Auto-responses for this project
choice:
  yn: yes
  '123': 1
  'path': './src'

# Custom key bindings
keybinding:
  prev_window: "M-Left"
  next_window: "M-Right"
```

### `.yesman/projects.yaml`
```yaml
# Project sessions
sessions:
  # Main development session
  saas-dev:
    session_name: "${USER}-saas-dev"
    start_directory: "${PWD}"
    environment:
      PROJECT_NAME: "my-saas-app"
      ENVIRONMENT: "development"
    before_script: |
      source scripts/setup-dev.sh
    windows:
      - window_name: "orchestration"
        layout: "even-horizontal"
        panes:
          - claude --dangerously-skip-permissions
          - command: "docker-compose up"
            name: "services"
      
      - window_name: "frontend"
        layout: "main-vertical"
        panes:
          - command: "cd frontend && npm run dev"
            name: "react-dev"
          - command: "cd frontend && npm run test:watch"
            name: "tests"
      
      - window_name: "backend"
        layout: "main-vertical"
        panes:
          - command: "cd backend && uvicorn app:app --reload"
            name: "api"
          - command: "cd backend && celery -A app worker"
            name: "worker"
      
      - window_name: "mobile"
        panes:
          - command: "cd mobile && npm run start"
            name: "metro"
      
      - window_name: "monitoring"
        layout: "tiled"
        panes:
          - command: "docker stats"
            name: "docker"
          - command: "tail -f logs/*.log"
            name: "logs"
          - command: "ngrok http 8000"
            name: "tunnel"
          - command: "redis-cli monitor"
            name: "redis"

  # Database management session
  saas-db:
    session_name: "${USER}-saas-db"
    start_directory: "${PWD}/backend"
    windows:
      - window_name: "database"
        layout: "even-horizontal"
        panes:
          - claude
          - command: "pgcli -d saas_dev"
            name: "postgres"
          - command: "redis-cli"
            name: "redis"
      
      - window_name: "migrations"
        panes:
          - command: "alembic history"
            name: "history"
          - command: "python manage_db.py"
            name: "manager"

  # Testing session
  saas-test:
    session_name: "${USER}-saas-test"
    start_directory: "${PWD}"
    environment:
      ENVIRONMENT: "test"
      DATABASE_URL: "postgresql://localhost/saas_test"
    windows:
      - window_name: "testing"
        layout: "tiled"
        panes:
          - claude
          - command: "cd frontend && npm run test:e2e"
            name: "e2e"
          - command: "cd backend && pytest"
            name: "api-tests"
          - command: "cd mobile && npm run test"
            name: "mobile-tests"
      
      - window_name: "coverage"
        panes:
          - command: "cd frontend && npm run coverage"
            name: "frontend-cov"
          - command: "cd backend && pytest --cov"
            name: "backend-cov"

  # Documentation session
  saas-docs:
    session_name: "${USER}-saas-docs"
    start_directory: "${PWD}/docs"
    windows:
      - window_name: "documentation"
        layout: "even-horizontal"
        panes:
          - claude
          - command: "mkdocs serve"
            name: "docs-server"
          - command: "npm run api-docs"
            name: "api-docs"
```

### `scripts/setup-dev.sh`
```bash
#!/bin/bash
# Development environment setup

echo "🚀 Setting up SaaS development environment..."

# Check Docker
if ! docker info > /dev/null 2>&1; then
  echo "❌ Docker is not running. Please start Docker Desktop."
  exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
  echo "❌ Node.js not found. Please install Node.js 18+"
  exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
  echo "❌ Python not found. Please install Python 3.11+"
  exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
(cd frontend && npm install)
(cd backend && pip install -r requirements.txt)
(cd mobile && npm install)

# Setup databases
echo "🗄️ Setting up databases..."
docker-compose up -d postgres redis

# Wait for postgres
echo "⏳ Waiting for PostgreSQL..."
until docker-compose exec -T postgres pg_isready; do
  sleep 1
done

# Run migrations
echo "🔄 Running database migrations..."
(cd backend && alembic upgrade head)

# Create test data
echo "🌱 Seeding development data..."
(cd backend && python scripts/seed_dev_data.py)

echo "✅ Development environment ready!"
```

## Usage

### 1. Initial Setup
```bash
# Clone the repository
git clone https://github.com/mycompany/my-saas-app.git
cd my-saas-app

# Start all development sessions
yesman up saas-dev saas-db

# Or start specific session
yesman up saas-test
```

### 2. Daily Development
```bash
# Start development
yesman up saas-dev

# Attach to existing session
yesman attach saas-dev

# Stop all sessions
yesman down
```

### 3. Running Tests
```bash
# Start test session
yesman up saas-test

# Run specific test suite
yesman exec saas-test "cd backend && pytest tests/api/"
```

### 4. Team Collaboration
```bash
# Each developer gets their own session
# Sessions are prefixed with username
yesman ls  # Shows: john-saas-dev, jane-saas-dev, etc.

# Share tmux session for pair programming
tmux attach -t ${USER}-saas-dev -r  # Read-only
```

## Tips

1. **Use environment variables** for personal settings:
   ```bash
   export YESMAN_CLAUDE_ARGS="--dangerously-skip-permissions"
   export PROJECT_ROOT="$HOME/work/my-saas-app"
   ```

2. **Create aliases** for common operations:
   ```bash
   alias saas="cd ~/work/my-saas-app && yesman up saas-dev"
   alias saas-test="yesman up saas-test"
   ```

3. **Customize for your workflow**:
   - Modify window layouts
   - Add/remove panes
   - Adjust commands for your tools

4. **Use templates** for similar projects:
   - Extract common patterns to templates
   - Override only what's different

## Troubleshooting

### Session won't start
```bash
# Check if session already exists
tmux ls | grep saas

# Force recreate
yesman down saas-dev && yesman up saas-dev
```

### Commands fail in panes
```bash
# Debug by attaching to session
yesman attach saas-dev

# Check logs
tail -f logs/yesman/*.log
```

### Permission issues
```bash
# Ensure scripts are executable
chmod +x scripts/*.sh

# Check Docker permissions
docker ps  # Should work without sudo
```