# Ollama Refactor Plan

## Overview
Remove all references to "ollama" and "detect_api_type" from the codebase to create a unified API client that treats all endpoints uniformly using OpenAI ChatCompletion format.

## Current State Analysis
The current `LLMClient` implementation already uses a unified approach with OpenAI ChatCompletion format for all API calls, but still contains:
- Ollama-specific code comments and logic
- Special handling for "ollama" API key
- Ollama-specific test classes and methods
- Documentation references to Ollama as a separate API type
- Skipped tests for removed `_detect_api_type()` method

## Changes Required

### 1. Code Changes (`giv/lib/llm.py`)
- [ ] Remove Ollama references from module docstring
- [ ] Remove special "ollama" handling in authorization logic
- [ ] Remove Ollama format parsing in `_extract_content()`
- [ ] Update comments to reflect unified API approach

### 2. Test File Changes (`tests/test_lib_llm.py`)
- [ ] Remove entire `TestLLMClientAPIDetection` class (already skipped)
- [ ] Remove entire `TestLLMClientOllamaAPI` class 
- [ ] Remove `test_generate_dry_run_ollama()` method
- [ ] Remove Ollama-specific URL building tests (already skipped)
- [ ] Remove `test_full_ollama_workflow()` method
- [ ] Update remaining test method names and descriptions to be API-agnostic

### 3. Documentation Changes
- [ ] Update `docs/configuration.md` - remove "Local Ollama Setup" section
- [ ] Update `docs/installation.md` - remove Ollama requirement
- [ ] Update `docs/architecture.md` - remove Ollama references
- [ ] Update `README.md` - remove Ollama-specific examples and references

### 4. Known Issues Cleanup
- [ ] Remove Ollama-related entries from `known-issues.md`
- [ ] Remove `detect_api_type` entries from `known-issues.md`

## Detailed File Changes

### File: `giv/lib/llm.py`

**Lines to modify:**
- Line 6: Remove "Ollama" from API formats comment
- Lines 159-167: Remove Ollama-specific authorization logic 
- Lines 233-235: Remove Ollama format parsing
- Line 162: Remove "ollama" from excluded API keys

### File: `tests/test_lib_llm.py`

**Classes/methods to remove:**
- `TestLLMClientAPIDetection` (lines 66-102) - already skipped
- `TestLLMClientOllamaAPI` (lines 105-200+)  
- `test_generate_dry_run_ollama` (lines 313-320)
- Ollama URL building tests (already skipped)
- `test_full_ollama_workflow` (lines 432-470+)

### File: `docs/configuration.md`

**Sections to modify:**
- Line 18: Remove "(OpenAI, Ollama, etc.)" - change to "(OpenAI, etc.)"
- Lines 100-104: Remove entire "Local Ollama Setup" section

### File: `docs/installation.md`

**Lines to modify:**
- Line 6: Remove Ollama requirement

### File: `docs/architecture.md`

**Lines to modify:**
- Line 132: Remove Ollama references from llm.sh description
- Line 161: Remove Ollama from optional dependencies list

### File: `README.md`

**Lines to modify:**
- Line 12: Change "OpenAI, Anthropic, Ollama, and custom endpoints" to "OpenAI, Anthropic, and custom endpoints"
- Lines 218+: Remove "Local Models (Ollama)" section

### File: `known-issues.md`

**Sections to remove:**
- Lines 14-23: "LLMClient API Detection Tests" section
- Lines 29-31: Ollama URL building test references

## Testing Strategy

After implementing changes:
1. Run full test suite to ensure no regressions
2. Verify all Ollama references are removed from codebase
3. Confirm documentation is consistent with unified API approach
4. Test that localhost APIs still work without special handling

## Acceptance Criteria

- [ ] All `grep -r "ollama"` searches return only README historical references (if any)
- [ ] All `grep -r "detect_api_type"` searches return no results
- [ ] All tests pass
- [ ] Documentation is consistent and doesn't mention Ollama as special case
- [ ] LLMClient works uniformly with all API endpoints
- [ ] No special case logic remains for different API types

## Implementation Order

1. Remove test code first (safest, won't break functionality)
2. Update implementation code (core logic changes)
3. Update documentation (user-facing changes)
4. Clean up known-issues.md (housekeeping)
5. Run full test suite and verify acceptance criteria
