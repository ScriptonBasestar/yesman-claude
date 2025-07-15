# Chrome DevTools Integration

## Overview

The Yesman Claude Dashboard includes Chrome DevTools Workspace integration for enhanced development experience. This
feature allows you to edit source files directly from Chrome DevTools and see changes reflected in your local file
system.

## Setup

### Prerequisites

- Node.js and npm installed
- SvelteKit project configured in `tauri-dashboard/`
- Chrome browser (or Chromium-based browser)

### Installation

The DevTools integration is already installed via the `vite-plugin-devtools-json` plugin. To verify installation:

```bash
# Check package.json for the plugin
cat tauri-dashboard/package.json | grep vite-plugin-devtools-json
```

### Configuration

The integration is configured in `tauri-dashboard/vite.config.ts`:

```typescript
import devtoolsJson from 'vite-plugin-devtools-json';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig(({ mode }) => ({
  plugins: [
    sveltekit(),
    // DevTools integration only in development
    mode === 'development' && devtoolsJson()
  ].filter(Boolean),
  // ... rest of config
}));
```

## Usage

### Enabling DevTools Workspace

1. Start the development server:

   ```bash
   cd tauri-dashboard
   npm run dev
   ```

1. Open Chrome DevTools (F12 or right-click → Inspect)

1. Navigate to `Settings` → `Workspace` in DevTools

1. Click "Add folder to workspace" and select your project directory

1. Chrome will automatically detect the DevTools configuration at:

   ```
   http://localhost:5173/.well-known/appspecific/com.chrome.devtools.json
   ```

### Editing Files

Once workspace is enabled:

- Edit files directly in the Sources panel
- Changes are saved to your local file system
- Hot Module Replacement (HMR) reflects changes immediately

### Verifying Integration

Check the DevTools endpoint:

```bash
curl http://localhost:5173/.well-known/appspecific/com.chrome.devtools.json
```

Expected response:

```json
{
  "workspace": {
    "root": "/path/to/your/tauri-dashboard",
    "uuid": "generated-uuid-here"
  }
}
```

## Security Considerations

⚠️ **IMPORTANT SECURITY WARNINGS**

### Development-Only Feature

- The DevTools integration is **ONLY** active in development mode
- Production builds automatically exclude this functionality
- Never expose DevTools endpoints in production environments

### File System Access

- DevTools Workspace grants Chrome access to your local file system
- Only add trusted folders to your workspace
- Be cautious when working with sensitive files

### Network Security

- The DevTools endpoint is only accessible on localhost
- Do not expose port 5173 to external networks
- Use firewall rules to restrict access if needed

### Environment Separation

The plugin is conditionally loaded based on Vite's mode:

```typescript
mode === 'development' && devtoolsJson()
```

This ensures production builds never include DevTools functionality.

## Troubleshooting

### Common Issues

#### DevTools endpoint returns 404

- **Cause**: Running in production mode
- **Solution**: Ensure you're using `npm run dev` not `npm run build && npm run preview`

#### Workspace not detecting project

- **Cause**: Chrome permissions or misconfiguration
- **Solution**:
  1. Remove and re-add the workspace folder
  1. Check Chrome has file system permissions
  1. Verify the DevTools endpoint is accessible

#### Changes not saving to disk

- **Cause**: File permissions or Chrome security restrictions
- **Solution**:
  1. Ensure you have write permissions for project files
  1. Check Chrome DevTools console for errors
  1. Try running Chrome with `--allow-file-access-from-files` flag (development only)

#### UUID changes on restart

- **Cause**: Normal behavior - UUID is generated per session
- **Solution**: This is expected and doesn't affect functionality

### Debug Commands

```bash
# Check if dev server is running
ps aux | grep "npm run dev"

# Test DevTools endpoint
curl -I http://localhost:5173/.well-known/appspecific/com.chrome.devtools.json

# Check Vite configuration
cat tauri-dashboard/vite.config.ts | grep devtools

# Verify plugin installation
npm list vite-plugin-devtools-json
```

## Advanced Configuration

### Custom Port Configuration

If using a different port, update `vite.config.ts`:

```typescript
server: {
  port: 3000,  // Your custom port
  strictPort: true
}
```

### Conditional Features

You can extend the DevTools configuration:

```typescript
plugins: [
  sveltekit(),
  mode === 'development' && process.env.ENABLE_DEVTOOLS !== 'false' && devtoolsJson()
].filter(Boolean)
```

### Integration with Tauri

When running in Tauri desktop mode, DevTools integration works seamlessly:

```bash
npm run tauri:dev
```

## Best Practices

1. **Always verify environment**: Double-check you're in development mode
1. **Use version control**: Commit changes before using DevTools editing
1. **Regular backups**: Keep backups when experimenting with file edits
1. **Monitor console**: Watch for errors or warnings in DevTools console
1. **Test production builds**: Regularly verify DevTools is disabled in production

## Additional Resources

- [Chrome DevTools Workspace Documentation](https://developer.chrome.com/docs/devtools/workspaces/)
- [Vite Plugin DevTools JSON](https://github.com/sveltejs/vite-plugin-svelte/tree/main/packages/vite-plugin-devtools-json)
- [SvelteKit Documentation](https://kit.svelte.dev/)

______________________________________________________________________

**Note**: This feature enhances development workflow but should never be enabled in production environments. Always
follow security best practices when granting file system access to browser applications.
