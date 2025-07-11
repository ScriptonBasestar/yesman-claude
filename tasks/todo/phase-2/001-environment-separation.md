# Environment Separation for DevTools

## Task Overview
Ensure DevTools integration is only active in development environment and properly disabled in production.

## Priority
High

## Estimated Time
15 minutes

## Prerequisites
- DevTools addon is installed and configured
- Understanding of Vite environment variables

## Steps

1. **Review current Vite configuration**
   - Open `tauri-dashboard/vite.config.js`
   - Verify plugin is conditionally loaded for development only

2. **Implement environment check**
   ```javascript
   // Expected configuration
   plugins: [
     sveltekit(),
     // DevTools integration only in development
     process.env.NODE_ENV === 'development' && devtoolsJson()
   ].filter(Boolean)
   ```

3. **Test production build**
   ```bash
   cd tauri-dashboard
   npm run build
   ```

4. **Verify production safety**
   - Check that DevTools endpoint is not accessible in production build
   - Ensure no DevTools-related code is included in production bundle

## Expected Outcome
- DevTools functionality is completely disabled in production
- Production build does not include DevTools-related code
- No security vulnerabilities in production deployment

## Verification Steps
- [ ] Production build completes without DevTools plugin
- [ ] DevTools endpoint returns 404 in production build
- [ ] No DevTools-related warnings in production console
- [ ] Bundle size is not affected by DevTools code

## Related Files
- `tauri-dashboard/vite.config.js`
- Production build output
- Network tab in production environment

## Next Steps
- Verify FastAPI server integration needs
- Test with different build environments

## Security Considerations
- **Critical**: DevTools must never be active in production
- File system access should be restricted to development only
- No sensitive project information should be exposed in production

## Notes
- This is a security-critical task
- Production deployment should be tested thoroughly
- Consider adding environment variable checks for additional safety