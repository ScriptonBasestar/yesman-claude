# Dashboard Configuration Guide

## Port Configuration

When running the dashboard in development mode with `uv run ./yesman.py dashboard run -i web --dev`, the following ports are used:

### Development Mode Ports

- **FastAPI Server**: `localhost:8000`
  - Main backend API server
  - Handles all `/api/*` endpoints
  - Health check: `http://localhost:8000/healthz`
  - API docs: `http://localhost:8000/docs`

- **Vite Dev Server**: `localhost:5173`
  - Frontend development server with hot module replacement
  - Main dashboard interface
  - Proxy configuration automatically forwards `/api` requests to port 8000

### API Configuration

The frontend uses **relative URLs** for API calls (e.g., `/api/dashboard/sessions`) which are automatically proxied by Vite to the FastAPI server. This configuration is defined in:

- **Frontend**: `tauri-dashboard/src/lib/utils/tauri.ts` - `API_BASE_URL = '/api'`
- **Proxy**: `tauri-dashboard/vite.config.ts` - Proxy `/api` to `http://localhost:8000`

### Usage

1. **Start Development Mode**:
   ```bash
   uv run ./yesman.py dashboard run -i web --dev
   ```

2. **Access Dashboard**:
   - Open browser to: `http://localhost:5173` (Vite dev server)
   - API endpoints available at: `http://localhost:8000/api/*` (FastAPI server)

3. **Verify Setup**:
   ```bash
   # Test FastAPI server
   curl http://localhost:8000/healthz
   
   # Test API endpoint
   curl http://localhost:8000/api/dashboard/sessions
   
   # Test Vite proxy
   curl http://localhost:5173/api/dashboard/sessions
   ```

### Troubleshooting

- **Port 8000 in use**: Change port with `-p` option: `--port 8001`
- **Port 5173 in use**: Vite will automatically find next available port
- **API timeouts**: Ensure both servers are running and proxy is configured correctly
- **CORS issues**: FastAPI is configured to allow all origins in development mode

## Production Configuration

In production, the dashboard runs as a single server on the specified port (default 8000) with the Svelte build served statically.