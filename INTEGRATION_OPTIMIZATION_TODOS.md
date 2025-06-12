# Gmail Spam Bot Integration & Optimization Guide - TODO List

## 1. Unify LLM Integration for LM Studio

### 1.1. Refactor autonomous_runner.py for Batch Analysis
- [x] Modify `run_batch_analysis` function to use LM Studio instead of Gemini
- [x] Replace Gemini-specific calls with `analyze_email_subjects_with_lm_studio`
- [x] Update configuration update logic for LM Studio output format

### 1.2. Implement update_config_from_lm_analysis
- [x] Create `update_config_from_lm_analysis` function in `lm_studio_integration.py`
- [x] Adapt logic from `gemini_config_updater.py` for LM Studio output
- [x] Integrate with autonomous runner workflow

## 2. Implement Smart Model Selection

### 2.1. Acknowledge API Limitations
- [ ] Document that remote model loading is not possible via LM Studio API
- [ ] Update code comments to clarify limitations

### 2.2. Implement Smart Selection Strategy
- [x] Modify `LMStudioManager.generate_completion` to remove non-functional `load_model` call
- [x] Add logic to detect currently loaded model ID
- [x] Implement graceful failure when no model is loaded
- [x] Use actual loaded model ID in API requests

## 3. Resolve Authentication Issues

### 3.1. Primary Action: Delete Stale Token
- [ ] Implement automatic stale token detection and cleanup
- [ ] Add warning messages for token refresh issues
- [ ] Update start.sh warnings about token refresh

### 3.2. Consolidate Authentication Logic
- [x] Enhance `get_gmail_service` in `gmail_api_utils.py` with robust error handling
- [x] Add token deletion logic on refresh failure to `gmail_api_utils.py`
- [x] Refactor `gmail_lm_cleaner.py` to use unified authentication from `gmail_api_utils.py`
- [x] Remove redundant authentication code

## 4. Enhance Stability and Process Management

### 4.1. Implement PID File Management
- [x] Add PID file creation to `autonomous_runner.py`
- [x] Add PID file creation to `bulk_processor.py`
- [x] Implement try...finally blocks for PID cleanup
- [x] Update `stop.sh` to use PID files for graceful shutdown
- [x] Add SIGTERM handling before pkill fallback

### 4.2. Use Systemd for Production
- [ ] Review existing systemd unit files from setup.sh
- [ ] Create production-ready systemd service configuration
- [ ] Add auto-restart policies and logging configuration
- [ ] Document systemd installation and management procedures

## Priority Order
1. **HIGH**: Authentication consolidation and stale token cleanup
2. **HIGH**: LM Studio integration in autonomous runner
3. **MEDIUM**: Smart model selection improvements
4. **MEDIUM**: PID file management and process stability
5. **LOW**: Systemd production setup

---
**Status**: 🚀 Ready to begin implementation
**Last Updated**: 2025-06-12