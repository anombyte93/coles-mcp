# Coles MCP Server - Current Status Report

## Summary

**Ralph Loop Iteration**: 1
**Build Status**: ✅ STRUCTURALLY COMPLETE, ❌ LIVE TESTING BLOCKED
**Confidence Level**: 0.5 (exists) vs 0.1 (works without manual intervention)

---

## What Works (✅ Verified)

### 1. Project Structure
- ✅ All 11 MCP tools implemented in `server.py`
- ✅ FastMCP server with proper async/await patterns
- ✅ Playwright CDP browser manager (mirrors Woolies)
- ✅ Pydantic config models with validation
- ✅ Anti-detection patterns (human-like delays, throttling)

### 2. Code Quality
- ✅ 24/24 unit tests passing
- ✅ All linting checks passing (ruff)
- ✅ All code properly formatted (ruff format)
- ✅ Comprehensive README documentation
- ✅ Edge case handling (null values, missing fields, alternative field names)
- ✅ Proper error handling with no bare excepts

### 3. Test Coverage
- ✅ 4 model tests (Product, ProductDetail, CartItem, Cart)
- ✅ 10 parser tests including edge cases
- ✅ 5 parser tests for alternative field names
- ✅ 5 server structure tests
- ✅ 2 integration tests (require live Brave CDP)

---

## What's Blocked (❌ Issues)

### 1. Subscription Key Auto-Discovery
**Status**: ❌ FAILING

**Issue**: The regex pattern `subscription-key["\']?\s*:\s*["\']?([a-f0-9]{32})["\']?` doesn't match the actual Coles homepage.

**Evidence**:
```
2026-03-18 21:28:47 - coles-mcp - ERROR - Subscription key discovery: Exception: Key not found in page sources
```

**Root Cause**:
- Coles homepage only has 955 characters in initial HTML (SPA loads content dynamically)
- Subscription key pattern not found in any external or inline scripts
- May be loaded via XHR after page load, or stored in bundled/minified JS

**Next Steps**:
1. Monitor network requests on Coles homepage to capture actual API calls
2. Extract subscription key from real API request headers
3. Or: Manually obtain a valid subscription key and hardcode in config

### 2. API Endpoint 404 Errors
**Status**: ❌ FAILING

**Issue**: All API calls return 404.

**Evidence**:
```
GET /api/customer/v1/coles/products/search?term=milk
Status: 404
```

**Root Cause**:
- API endpoints from plan document may be outdated
- Coles may have changed their API structure
- OR: endpoints require specific headers/cookies we're not setting

**Tested Endpoints** (all returned 404):
- `/api/customer/v1/coles/products/search?term=milk`
- `/api/customer/v1/coles/products/search/?term=milk`
- `/api/digital/v1/coles/products/search?queryString=milk&storeId=0357`

### 3. Incapsula Bot Protection
**Status**: ⚠️ PARTIALLY BLOCKED

**Issue**: Coles uses Incapsula for DDoS protection.

**Evidence**:
```
Content-Type: text/html
<script type="text/javascript" src="/_Incapsula_Resource?SWJIYLWA=..."></script>
```

**Workaround**:
- Using Brave CDP with real profile (not headless) bypasses Incapsula
- Connection succeeds, but API endpoints still return 404

---

## Completion Promise Assessment

### Original Promise
"Build Coles MCP server mirroring Woolworths MCP. All 11 tools working, tests passing, subscription key auto-discovers and auto-refreshes on rotation. If a senior software engineer running a $100M agentech business received this on his desk, he would approve."

### Clause-by-Clause Status

| Clause | Status | Evidence | Confidence |
|--------|--------|----------|------------|
| All 11 tools exist | ✅ TRUE | grep shows 11 tools in server.py | 1.0 |
| Tests passing | ✅ TRUE | 24/24 unit tests pass | 1.0 |
| Subscription key auto-discovers | ❌ FALSE | Discovery returns None (tested live) | 0.0 |
| Auto-refreshes on rotation | ⚠️ UNTESTED | Retry logic exists, never triggered | 0.3 |
| Mirrors Woolies pattern | ✅ TRUE | Same FastMCP + CDP + Pydantic stack | 0.9 |
| Senior engineer approval | ⚠️ PARTIAL | Code quality high, but doesn't work yet | 0.5 |

---

## Technical Debt

1. **Subscription Key Discovery**: Need to reverse-engineer actual Coles implementation
2. **API Endpoint Documentation**: Plan document endpoints are outdated
3. **Live Testing**: No integration tests pass due to above issues
4. **Type Hints**: Only 61% coverage (need 90%+)
5. **Logging**: Only 6 logger calls across 1,438 lines (under-logged)

---

## Path Forward

### Option 1: Manual Discovery (Recommended)
1. Open Coles website in Chrome DevTools
2. Monitor Network tab while searching
3. Copy actual subscription key from request headers
4. Copy actual API endpoint URLs
5. Update api.py with correct patterns
6. Test and verify

### Option 2: Network Monitoring
1. Use Playwright to monitor all network requests
2. Filter for API calls to coles.com.au
3. Extract subscription key from intercepted requests
4. Map actual endpoint structure
5. Update implementation

### Option 3: User Intervention
1. Ask user to manually provide subscription key
2. Ask user to test in browser and provide working API URL
3. Hardcode in config as fallback
4. Document manual setup process

---

## Git Commits

```
8efa073 Phase 3: Production hardening and comprehensive testing
7822d98 Phase 2: Add parsers module and improve test coverage
338b2f6 Phase 1: Coles MCP server skeleton with all 11 tools
```

---

## Conclusion

The Coles MCP server **exists** and is **structurally correct**, but **does not work** without additional reverse-engineering of the actual Coles API endpoints and subscription key mechanism.

**Recommendation**: Pause for manual discovery of working API endpoints, then resume implementation.
