# Install SvelteKit DevTools Addon

## Task Overview
Install the official SvelteKit devtools-json addon to enable Chrome DevTools integration.

## Priority
High

## Estimated Time  
30 minutes

## Prerequisites
- SvelteKit project is set up in `tauri-dashboard/`
- Node.js and npm are installed

## Steps

1. **Navigate to the Tauri dashboard directory**
   ```bash
   cd tauri-dashboard
   ```

2. **Install the devtools-json addon**
   ```bash
   npx sv add devtools-json
   ```

3. **Verify installation**
   - Check that `vite-plugin-devtools-json` is added to `package.json`
   - Verify `vite.config.js` has been updated with the plugin

## Expected Outcome
- The `vite-plugin-devtools-json` plugin should be installed
- The plugin should be configured in `vite.config.js`
- Development server should be ready for the next configuration step

## Verification Steps
- [x] Plugin appears in `package.json` dependencies
- [x] Plugin is configured in `vite.config.js`
- [x] No installation errors occurred

## Related Files
- `tauri-dashboard/package.json`
- `tauri-dashboard/vite.config.js`

## Next Steps
- Configure and test the DevTools integration
- Verify the `.well-known/appspecific/com.chrome.devtools.json` endpoint

## Notes
- This is the official SvelteKit solution for Chrome DevTools integration
- The addon automatically handles the DevTools configuration JSON file