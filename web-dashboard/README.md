# Yesman Claude Web Dashboard

Web-based dashboard interface for Yesman Claude.

## Setup

1. Install dependencies:
```bash
cd web-dashboard
npm install
```

2. Run development server:
```bash
npm run dev
```

3. Build for production:
```bash
npm run build
```

## Project Structure

```
web-dashboard/
├── static/
│   ├── js/
│   │   ├── components/    # Web components
│   │   ├── utils/         # Utility functions
│   │   └── main.js        # Entry point
│   ├── css/
│   │   ├── components/    # Component styles
│   │   ├── themes/        # Theme files
│   │   └── main.css       # Main stylesheet
│   └── templates/         # HTML templates
├── tests/                 # Test files
├── build.js              # Build configuration
├── tailwind.config.js    # Tailwind CSS config
├── package.json          # NPM dependencies
├── .eslintrc.json        # ESLint config
└── .prettierrc           # Prettier config
```

## Technologies

- **Build**: esbuild
- **CSS**: Tailwind CSS
- **JS Framework**: Alpine.js
- **HTTP Client**: Axios
- **WebSocket**: Socket.io Client
- **Charts**: Chart.js

## Development

The build system uses esbuild for fast bundling and hot reload in development mode.