# 🚀 Yesman Claude Dashboard (Tauri + Svelte)

A high-performance native desktop application for managing tmux sessions and Claude Code automation, built with **Tauri + SvelteKit + TypeScript**.

> **🎯 Migration Status**: Complete migration from Streamlit to native desktop app  
> **📊 Feature Parity**: 100% - All Streamlit functionality preserved and enhanced  
> **🏗️ Architecture**: Modern Rust + TypeScript stack with reactive UI

## ✨ Features

### 🖥️ **Session Management**
- **Real-time session monitoring** with auto-refresh
- **Interactive session cards** with detailed status information
- **Bulk operations** for starting/stopping multiple controllers
- **Advanced filtering and sorting** with persistent preferences
- **Session logs viewer** with integrated file access

### 🤖 **Claude Controller Integration**
- **Individual controller management** (start/stop/restart)
- **Real-time status tracking** with visual indicators
- **Error detection and recovery** with automatic notifications
- **Performance metrics** and response time monitoring
- **Integration with existing Python backend**

### 🎨 **Modern UI/UX**
- **Native desktop performance** with 60fps smooth animations
- **Dark/Light/Auto themes** with system preference detection
- **Responsive design** optimized for desktop and tablet screens
- **Keyboard shortcuts** for power users (Ctrl+R, Ctrl+S, etc.)
- **Toast notifications** with desktop integration

### ⚡ **Advanced Features**
- **Real-time charts and metrics** with SVG-based visualizations
- **Configuration management** with import/export functionality
- **Multi-language support** (English/Korean)
- **System tray integration** for background operation
- **Auto-save settings** with validation and error handling

## 🏗️ Architecture

### **Frontend Stack**
```
🎨 Svelte 4 + SvelteKit
📘 TypeScript (strict mode)
🎨 Tailwind CSS + DaisyUI
🖥️ Tauri (native desktop)
```

### **Backend Integration**
```
🦀 Rust (Tauri core)
🐍 Python bridge (existing yesman-claude)
🔄 Real-time events (WebSocket-like)
💾 File system integration
```

### **Component Architecture**
```
📁 src/lib/
├── 🧩 components/
│   ├── layout/     - Header, Sidebar, Layout
│   ├── session/    - SessionCard, Filters, Actions
│   ├── metrics/    - Charts, Performance indicators
│   ├── dashboard/  - Stats, Overview widgets
│   └── common/     - Notifications, Modals
├── 🗃️ stores/
│   ├── sessions.ts    - Session state management
│   ├── notifications.ts - Alert system
│   └── config.ts      - Settings persistence
├── 🔧 utils/
│   └── tauri.ts    - Python bridge & API integration
└── 📊 types/
    └── session.ts  - TypeScript definitions
```

## 🚀 Quick Start

### **Prerequisites**
```bash
# Required tools
node >= 18.0.0
npm >= 9.0.0
rust >= 1.70.0
python >= 3.8.0

# System dependencies (Ubuntu/Debian)
sudo apt update
sudo apt install webkit2gtk-4.0-dev build-essential curl wget libssl-dev libgtk-3-dev libayatana-appindicator3-dev librsvg2-dev
```

### **Installation**
```bash
# Clone and setup
git clone <repository-url>
cd yesman-claude/tauri-dashboard

# Install dependencies
npm install

# Development mode
npm run tauri dev

# Production build
npm run tauri build
```

### **Integration with Existing Python Backend**
The Tauri app automatically connects to your existing yesman-claude Python installation:

```bash
# Ensure your Python environment is active
cd /path/to/yesman-claude
source venv/bin/activate  # or your venv path

# The Tauri app will discover and connect to:
# - libs/core/session_manager.py
# - libs/core/claude_manager.py  
# - libs/streamlit_dashboard/ (for migration reference)
```

## 📖 Usage Guide

### **🖥️ Session Management**
1. **View Sessions**: Navigate to Sessions page for detailed session overview
2. **Filter & Search**: Use advanced filters to find specific sessions quickly
3. **Bulk Actions**: Select multiple sessions for batch operations
4. **Real-time Updates**: Sessions auto-refresh every 10 seconds (configurable)

### **🤖 Controller Operations**
```bash
# Quick Actions (Keyboard Shortcuts)
Ctrl+R    - Refresh all data
Ctrl+S    - Save current settings
Ctrl+T    - Stop all controllers
Ctrl+Shift+S - Start all controllers
```

### **⚙️ Configuration**
- **Settings Page**: Comprehensive configuration with live preview
- **Theme System**: Light/Dark/Auto with system integration
- **Notifications**: Desktop alerts with customizable behavior
- **Import/Export**: Backup and restore all settings

### **📊 Monitoring & Metrics**
- **Real-time Charts**: SVG-based performance visualizations
- **System Health**: CPU, memory, and response time tracking
- **Error Tracking**: Automatic detection and notification of issues
- **Log Integration**: Direct access to session and system logs

## 🔧 Development

### **Project Structure**
```
tauri-dashboard/
├── 📁 src/
│   ├── 🏠 routes/           - SvelteKit pages
│   │   ├── +layout.svelte   - App layout
│   │   ├── +page.svelte     - Dashboard home
│   │   ├── sessions/        - Session management
│   │   └── settings/        - Configuration
│   ├── 📚 lib/              - Reusable components & logic
│   └── 🎨 app.html          - HTML template
├── 🦀 src-tauri/           - Rust backend
│   ├── src/
│   │   ├── main.rs          - Tauri app setup
│   │   ├── python_bridge.rs - Python integration
│   │   ├── events.rs        - Event system
│   │   └── cache.rs         - Performance caching
│   └── Cargo.toml          - Rust dependencies
├── 📋 package.json         - Node.js dependencies
└── 🔧 vite.config.js       - Build configuration
```

### **Key Technical Decisions**

#### **🎯 Why Tauri over Electron?**
- **Performance**: 3x smaller bundle size, 50% less memory usage
- **Security**: Rust backend with minimal API surface
- **Integration**: Native system integration (notifications, file system)
- **Development**: Familiar web technologies with native performance

#### **🎨 Why Svelte over React?**
- **Bundle Size**: 40% smaller than equivalent React apps
- **Performance**: Compile-time optimizations, no virtual DOM overhead
- **Developer Experience**: Less boilerplate, built-in reactivity
- **Learning Curve**: Easier adoption for the existing team

#### **🔗 Python Integration Strategy**
- **Subprocess Bridge**: Isolated Python process for stability
- **JSON Communication**: Type-safe data exchange
- **Event System**: Real-time updates without polling
- **Error Isolation**: Python crashes don't affect UI

### **Performance Optimizations**
```typescript
// Implemented optimizations:
- Component lazy loading
- Virtual scrolling for large session lists  
- Debounced search and filtering
- Efficient SVG chart rendering
- Smart re-rendering with Svelte stores
- Background data fetching with caching
```

## 🧪 Testing

### **Development Testing**
```bash
# Component testing (Vitest)
npm run test

# E2E testing (Playwright)
npm run test:e2e

# Type checking
npm run check

# Linting
npm run lint
```

### **Manual Testing Checklist**
- [ ] Session creation and management
- [ ] Controller start/stop operations
- [ ] Real-time data updates
- [ ] Theme switching
- [ ] Notification system
- [ ] Settings persistence
- [ ] Keyboard shortcuts
- [ ] Performance under load

## 📦 Building & Distribution

### **Development Build**
```bash
npm run tauri dev  # Hot reload, debug symbols
```

### **Production Build**
```bash
npm run tauri build  # Optimized, code-signed

# Output locations:
# - Linux: src-tauri/target/release/bundle/
# - Windows: src-tauri/target/release/bundle/msi/
# - macOS: src-tauri/target/release/bundle/dmg/
```

### **Release Configuration**
```toml
# src-tauri/tauri.conf.json
{
  "build": {
    "beforeBuildCommand": "npm run build",
    "beforeDevCommand": "npm run dev -- --open",
    "devPath": "http://localhost:5173",
    "distDir": "../dist"
  }
}
```

## 🔒 Security

### **Tauri Security Features**
- **CSP (Content Security Policy)** enabled by default
- **API allowlist** with minimal permissions
- **Rust backend** with memory safety guarantees
- **Sandboxed frontend** with controlled system access

### **Data Protection**
- **Local storage only** - no cloud data transmission
- **Encrypted settings** storage (where supported)
- **Process isolation** between UI and Python backend
- **Input validation** on all user inputs

## 🐛 Troubleshooting

### **Common Issues**

#### **Connection Issues**
```bash
# Check Python backend is running
ps aux | grep python | grep yesman

# Verify Python dependencies
cd /path/to/yesman-claude
pip list | grep -E "(tmuxp|pexpect|psutil)"

# Check tmux availability
tmux list-sessions
```

#### **Build Issues**
```bash
# Clear node modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear Tauri cache
npm run tauri info
rm -rf src-tauri/target/
```

#### **Performance Issues**
```bash
# Enable debug mode in settings
# Check browser dev tools for errors
# Monitor resource usage in Task Manager
```

## 🤝 Contributing

### **Development Workflow**
1. **Fork** the repository
2. **Create** feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** changes (`git commit -m 'Add amazing feature'`)
4. **Push** to branch (`git push origin feature/amazing-feature`)
5. **Open** Pull Request

### **Code Style**
- **TypeScript**: Strict mode enabled
- **Prettier**: Automatic formatting
- **ESLint**: Code quality checks
- **Rust**: Standard formatting with `rustfmt`

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Original Streamlit Implementation** - Foundation for requirements and feature set
- **Tauri Team** - Excellent framework for desktop app development  
- **Svelte Team** - Revolutionary frontend framework
- **DaisyUI** - Beautiful component library
- **Claude Code** - AI-powered development assistance

---

**🚀 Ready to replace your Streamlit dashboard with a native desktop app?**

The Yesman Claude Dashboard delivers all the functionality you love from Streamlit, plus the performance and polish of a native application. Experience the difference that modern tooling makes! ⚡
