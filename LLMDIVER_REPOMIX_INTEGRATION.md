# LLMdiver Repomix Integration Documentation

## Current State Analysis

### LLMdiver's Current Implementation
- **Custom repomix emulation**: LLMdiver currently uses basic grep/tree commands to create a lightweight repo summary
- **No actual repomix**: Uses shell commands to extract TODOs, mocks/stubs, dead functions, and file structure
- **Limited functionality**: Only processes top 50 items per category

### Key Findings from LLMdiver Code Analysis

#### Current "repomix" Implementation in `run_llm_audit.sh`
```bash
# Lines 117-129: Basic repo summary generation
grep -rIn --exclude-dir={.git,node_modules,dist,build,venv,__pycache__,site-packages} -E 'TODO|FIXME' "$REPO_PATH" | head -n 50
grep -rIn --exclude-dir={.git,node_modules,dist,build,venv,__pycache__,site-packages} -E 'mock|stub|fake' "$REPO_PATH" | head -n 50
grep -rIn --exclude-dir={.git,node_modules,dist,build,venv,__pycache__,site-packages} -E 'def |function ' "$REPO_PATH" | head -n 50
tree -L 2 -I 'node_modules|dist|build|venv|__pycache__|.git|site-packages' "$REPO_PATH" | head -n 50
```

#### Enhanced "repomix" in `generate_repomix()` function (Lines 268-305)
- More sophisticated pattern matching
- Better file filtering with `--include` patterns
- Source file types: `*.{py,js,ts,jsx,tsx,sh}`
- Code file types: `*.{py,js,ts,jsx,tsx}`

## Integration Requirements

### 1. Real Repomix Integration
Replace the custom grep-based approach with actual repomix commands:

```bash
# Current approach (lines 117-129)
echo "🔀 Generating slimmed repo mix..." > "$SUMMARY_FILE"

# Proposed repomix integration
repomix "$REPO_PATH" \
  --output "$SUMMARY_FILE" \
  --style markdown \
  --compress \
  --remove-comments \
  --remove-empty-lines \
  --ignore "*.md" \
  --no-gitignore \
  --include "*.py,*.js,*.ts,*.jsx,*.tsx,*.sh" \
  --token-count-encoding cl100k_base
```

### 2. Gitignore Handling Challenge
**Key Issue**: Repomix respects `.gitignore` by default, but LLMdiver needs to track ALL files for comprehensive analysis.

#### Current LLMdiver Exclusions
- node_modules, dist, build, venv, __pycache__, .git, site-packages

#### Solution Options
1. **Use `--no-gitignore` flag**: Bypass gitignore completely
2. **Dynamic gitignore management**: Update `.gitignore` before each run
3. **Custom ignore patterns**: Use `--ignore` flag with specific patterns

### 3. .gitignore Update Strategy

#### Recommended Approach
```bash
# Backup original gitignore
cp .gitignore .gitignore.backup

# Create LLMdiver-specific gitignore
cat > .gitignore.llmdiver << EOF
# LLMdiver Analysis - Include everything except:
node_modules/
dist/
build/
venv/
__pycache__/
.git/
site-packages/
*.log
*.tmp
EOF

# Use during analysis
repomix --config-ignore .gitignore.llmdiver

# Restore original
mv .gitignore.backup .gitignore
```

### 4. Configuration Integration

#### Add to LLMdiver config (`config/llmdiver.json`)
```json
{
  "model": "codellama:7b-instruct",
  "source": "lmstudio",
  "repomix": {
    "enabled": true,
    "style": "markdown",
    "compress": true,
    "remove_comments": true,
    "remove_empty_lines": true,
    "include_patterns": ["*.py", "*.js", "*.ts", "*.jsx", "*.tsx", "*.sh"],
    "ignore_patterns": ["*.md", "*.log", "*.tmp"],
    "use_gitignore": false,
    "token_encoding": "cl100k_base"
  }
}
```

## Implementation Steps

### Phase 1: Basic Integration
1. Replace grep-based analysis with repomix calls
2. Add repomix configuration to `config/llmdiver.json`
3. Update `run_llm_audit.sh` to use real repomix

### Phase 2: Gitignore Management
1. Implement dynamic gitignore backup/restore
2. Create LLMdiver-specific ignore patterns
3. Add `--update-gitignore` flag to control behavior

### Phase 3: Advanced Features
1. Token counting and optimization
2. Diff integration for change tracking
3. Remote repository analysis support

## Command Line Integration

### Updated `run_llm_audit.sh` Usage
```bash
# Standard analysis with repomix
./run_llm_audit.sh /path/to/repo

# Force gitignore update
./run_llm_audit.sh /path/to/repo --update-gitignore  

# Use custom repomix config
./run_llm_audit.sh /path/to/repo --repomix-config custom.json

# Show repomix payload
./run_llm_audit.sh /path/to/repo --show-repomix-payload
```

### Repomix Revolution Cycle
Every LLMdiver analysis cycle should:
1. Backup current `.gitignore`
2. Apply LLMdiver ignore patterns
3. Run repomix analysis
4. Restore original `.gitignore`
5. Update LLMdiver tracking files

## Current Status
- ✅ Repomix installed globally (`npm install -g repomix`)
- ✅ LLMdiver architecture analyzed
- ⏳ Integration implementation needed
- ⏳ Gitignore management strategy to implement
- ⏳ Configuration updates required

## LLMdiver Background Daemon Architecture

### Core Requirements
1. **Background Processing**: Continuous monitoring and analysis
2. **Git Integration**: Automatic staging, commits, and documentation
3. **API Endpoints**: Interface for Claude Code / Roo Code
4. **Change Detection**: File system monitoring with intelligent triggers

### Daemon Architecture Design

#### 1. LLMdiver Daemon Components
```
LLMdiver Daemon (llmdiver-daemon.py)
├── FileWatcher (inotify/fsevents)
├── RepoMixProcessor (repomix integration)
├── LLMAnalyzer (LM Studio client)
├── GitAutomation (commit/push/doc)
├── APIServer (REST endpoints)
└── StateManager (persistence)
```

#### 2. Background Service Features
- **Continuous Monitoring**: Watch for file changes using `inotify` (Linux) or `fsevents` (macOS)
- **Intelligent Triggering**: Debounced analysis (avoid excessive runs)
- **Queue Management**: Process multiple repos concurrently
- **Health Monitoring**: Self-healing daemon with status reporting

#### 3. Git Automation Features
```bash
# Auto-commit workflow
1. Detect significant changes (> threshold)
2. Run repomix analysis
3. Generate LLM insights
4. Stage relevant files
5. Create descriptive commit message
6. Push to remote (if configured)
7. Generate/update documentation
```

#### 4. API Endpoints for Claude Code / Roo Code
```
GET  /status                    # Daemon health and repo status
GET  /repos                     # List monitored repositories  
POST /repos/{name}/analyze      # Trigger immediate analysis
GET  /repos/{name}/issues       # Get current issues/todos
GET  /repos/{name}/insights     # Get latest LLM insights
POST /repos/{name}/auto-fix     # Trigger automated fixes
GET  /repos/{name}/commits      # Recent auto-commits
```

### Implementation Plan

#### Phase 1: Daemon Foundation
1. Create `llmdiver-daemon.py` with basic file watching
2. Integrate real repomix instead of grep-based approach
3. Add configuration for monitoring multiple repos
4. Implement basic REST API server

#### Phase 2: Git Automation
1. Add git change detection and analysis
2. Implement intelligent commit message generation
3. Add auto-staging and push capabilities
4. Create documentation auto-generation

#### Phase 3: Advanced Integration
1. Add Claude Code / Roo Code webhook support
2. Implement issue tracking and resolution
3. Add performance metrics and reporting
4. Create web dashboard for monitoring

### Configuration Structure

#### Enhanced `config/llmdiver.json`
```json
{
  "daemon": {
    "enabled": true,
    "port": 8080,
    "host": "localhost",
    "log_level": "INFO",
    "watch_debounce": 5,
    "max_concurrent_analyses": 3
  },
  "repositories": [
    {
      "name": "GMAILspambot",
      "path": "/home/greenantix/AI/GMAILspambot",
      "auto_commit": true,
      "auto_push": false,
      "analysis_triggers": ["*.py", "*.js", "*.sh"],
      "commit_threshold": 10
    }
  ],
  "git_automation": {
    "enabled": true,
    "commit_message_template": "🤖 LLMdiver: {summary}\n\n{details}",
    "auto_push": false,
    "documentation_update": true,
    "branch_protection": ["main", "master"]
  },
  "llm_integration": {
    "model": "codellama:7b-instruct",
    "source": "lmstudio",
    "url": "http://127.0.0.1:1234/v1/chat/completions",
    "temperature": 0.3,
    "max_tokens": 4096
  },
  "repomix": {
    "style": "markdown",
    "compress": true,
    "remove_comments": true,
    "include_patterns": ["*.py", "*.js", "*.ts"],
    "ignore_patterns": ["*.md", "*.log"],
    "use_gitignore": false
  }
}
```

### Service Management

#### Systemd Service (`llmdiver.service`)
```ini
[Unit]
Description=LLMdiver Code Analysis Daemon
After=network.target

[Service]
Type=simple
User=greenantix
WorkingDirectory=/home/greenantix/AI/LLMdiver
ExecStart=/usr/bin/python3 llmdiver-daemon.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Service Commands
```bash
# Start daemon
sudo systemctl start llmdiver
sudo systemctl enable llmdiver

# Status and logs
sudo systemctl status llmdiver
journalctl -u llmdiver -f

# Integration with Claude Code
curl http://localhost:8080/repos/GMAILspambot/issues
```

## Next Steps
1. **Create daemon foundation**: Implement `llmdiver-daemon.py`
2. **Integrate real repomix**: Replace grep-based analysis
3. **Add git automation**: Implement auto-commit/push features
4. **Create API endpoints**: Enable Claude Code integration
5. **Test background processing**: Validate daemon functionality
6. **Add service management**: Systemd integration for auto-start