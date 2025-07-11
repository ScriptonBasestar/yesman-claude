# Chrome DevTools Integration QA Scenario

---
title: Chrome DevTools Integration End-to-End Testing
related_tasks:
  - /tasks/done/phase-1/001-install-devtools-addon__DONE_20250711.md
  - /tasks/done/phase-1/002-configure-and-test__DONE_20250711.md
  - /tasks/done/phase-2/001-environment-separation__DONE_20250711.md
  - /tasks/done/phase-2/002-fastapi-integration__DONE_20250711.md
purpose: Verify Chrome DevTools integration works correctly in development and is properly disabled in production
tags: [qa, e2e, manual, grouped, security]
---

## Prerequisites
- Node.js and npm installed
- Chrome browser (or Chromium-based browser)
- Access to development and production environments
- Git repository cloned locally

## Test Scenarios

### Scenario 1: DevTools Installation Verification
**Given**: A fresh SvelteKit project setup
**When**: Checking the installed dependencies
**Then**:
- [ ] `vite-plugin-devtools-json` appears in package.json devDependencies
- [ ] Plugin version is ^0.2.0 or higher
- [ ] vite.config.ts imports the plugin correctly

### Scenario 2: Development Environment DevTools Functionality
**Given**: Development server is not running
**When**: Starting the development server
```bash
cd tauri-dashboard
npm run dev
```
**Then**:
- [ ] Server starts without errors on port 5173
- [ ] Console may show "Generated UUID for DevTools project settings" message
- [ ] No DevTools-related errors in console

**When**: Accessing the DevTools endpoint
```bash
curl http://localhost:5173/.well-known/appspecific/com.chrome.devtools.json
```
**Then**:
- [ ] Returns valid JSON response with structure:
  ```json
  {
    "workspace": {
      "root": "/path/to/tauri-dashboard",
      "uuid": "generated-uuid-here"
    }
  }
  ```
- [ ] HTTP status code is 200
- [ ] Content-Type is application/json

### Scenario 3: Chrome DevTools Workspace Integration
**Given**: Development server is running
**When**: Opening Chrome DevTools
1. Navigate to http://localhost:5173
2. Open Chrome DevTools (F12)
3. Go to Settings → Workspace
4. Click "Add folder to workspace"
5. Select the project directory
**Then**:
- [ ] Chrome automatically detects the DevTools configuration
- [ ] No warning about missing `.well-known/appspecific/com.chrome.devtools.json`
- [ ] Workspace is successfully added
- [ ] File editing in Sources panel saves to local filesystem

### Scenario 4: Production Environment Security
**Given**: A production build exists
**When**: Building for production
```bash
cd tauri-dashboard
npm run build
```
**Then**:
- [ ] Build completes without DevTools plugin warnings
- [ ] No DevTools-related code in build output
- [ ] Build size is not affected by DevTools code

**When**: Running production preview
```bash
npm run preview
```
**And**: Accessing the DevTools endpoint
```bash
curl http://localhost:4173/.well-known/appspecific/com.chrome.devtools.json
```
**Then**:
- [ ] Returns 404 Not Found or SPA fallback HTML
- [ ] Does NOT return DevTools JSON configuration
- [ ] No security vulnerabilities exposed

### Scenario 5: FastAPI Integration Verification
**Given**: FastAPI server is configured
**When**: Starting the web dashboard
```bash
uv run ./yesman.py dash run -i web --port 8080
```
**Then**:
- [ ] Server starts successfully
- [ ] Dashboard accessible at http://localhost:8080
- [ ] API endpoints work correctly at /api/*

**When**: Accessing DevTools endpoint through FastAPI
```bash
curl http://localhost:8080/.well-known/appspecific/com.chrome.devtools.json
```
**Then**:
- [ ] Returns SPA fallback (index.html) not DevTools JSON
- [ ] No conflict between SvelteKit and FastAPI routing
- [ ] DevTools functionality is handled by SvelteKit only

### Scenario 6: Environment Configuration Testing
**Given**: vite.config.ts with environment-based plugin loading
**When**: Inspecting the configuration
```typescript
export default defineConfig(({ mode }) => ({
  plugins: [
    sveltekit(),
    mode === 'development' && devtoolsJson()
  ].filter(Boolean),
  // ...
}));
```
**Then**:
- [ ] Plugin is conditionally loaded based on mode
- [ ] `.filter(Boolean)` removes falsy values in production
- [ ] No TypeScript errors in configuration

## Security Validation

### Critical Security Checks
- [ ] DevTools endpoint is NOT accessible in production builds
- [ ] No file system access granted in production environment
- [ ] DevTools configuration does not expose sensitive paths
- [ ] Production bundle does not include DevTools plugin code

## Regression Testing

After any updates to the DevTools integration:
1. [ ] Re-run all scenarios above
2. [ ] Verify no new console warnings appear
3. [ ] Check that existing functionality remains intact
4. [ ] Ensure documentation is still accurate

## Performance Testing

- [ ] Development server startup time is not significantly impacted
- [ ] Production build time remains reasonable
- [ ] No memory leaks during extended DevTools usage
- [ ] File watching performance is acceptable

## Expected Results Summary

✅ **Development Environment**:
- DevTools fully functional
- Workspace integration works
- File editing capabilities enabled
- No console warnings

✅ **Production Environment**:
- DevTools completely disabled
- No security vulnerabilities
- No impact on bundle size
- Professional deployment ready

## Notes for QA Team

- This feature is DEVELOPMENT ONLY - emphasis on security testing
- Test on multiple browsers if possible (Chrome, Edge, Brave)
- Document any browser-specific behaviors
- Report any unexpected DevTools warnings immediately