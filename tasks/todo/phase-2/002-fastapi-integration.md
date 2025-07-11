# FastAPI Server DevTools Integration

## Task Overview
Review and optionally implement DevTools JSON endpoint in the FastAPI server for consistency.

## Priority
Medium

## Estimated Time
15 minutes

## Prerequisites
- Understanding of FastAPI routing system
- Knowledge of current API server architecture

## Steps

1. **Assess integration necessity**
   - Review how the dashboard is served (SvelteKit vs FastAPI)
   - Determine if FastAPI needs separate DevTools endpoint
   - Check if SvelteKit handles all DevTools requests

2. **If FastAPI integration is needed:**
   - Create `api/routers/devtools.py` (optional)
   - Add DevTools JSON endpoint:
     ```python
     @router.get("/.well-known/appspecific/com.chrome.devtools.json")
     async def devtools_config():
         # Development environment only
         return JSONResponse({
             "type": "node",
             "name": "Yesman Claude Dashboard API",
             "rootPath": "/home/archmagece/myopen/scripton/yesman-claude"
         })
     ```

3. **Add environment protection**
   - Implement development-only check
   - Return 404 in production environment

4. **Test integration**
   - Verify endpoint works in development
   - Confirm it's disabled in production

## Expected Outcome
- FastAPI server properly handles DevTools requests (if needed)
- Consistent behavior between SvelteKit and FastAPI servers
- Production safety is maintained

## Verification Steps
- [ ] Determine if FastAPI integration is necessary
- [ ] If implemented, endpoint works in development
- [ ] If implemented, endpoint is disabled in production
- [ ] No conflicts between SvelteKit and FastAPI DevTools endpoints

## Related Files
- `api/routers/devtools.py` (new file, if needed)
- `api/main.py` (for router registration)
- FastAPI server configuration

## Next Steps
- Move to Phase 3: Documentation
- Test complete integration

## Decision Points
- **Key Decision**: Is FastAPI DevTools endpoint needed?
- Most likely SvelteKit handles all DevTools requests
- FastAPI endpoint would be redundant unless dashboard is served differently

## Notes
- This may be optional depending on current architecture
- Focus on not duplicating functionality
- Ensure no conflicts between multiple DevTools endpoints