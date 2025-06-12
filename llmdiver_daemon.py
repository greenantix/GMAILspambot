#!/usr/bin/env python3
"""
LLMdiver Background Daemon
Monitors repositories, runs analysis, and automates git operations
"""

import os
import sys
import time
import json
import subprocess
import threading
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import signal

import git
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import requests

class LLMdiverConfig:
    def __init__(self, config_path: str = "config/llmdiver.json"):
        self.config_path = config_path
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """Load configuration from JSON file"""
        default_config = {
            "daemon": {
                "enabled": True,
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
                    "auto_commit": True,
                    "auto_push": False,
                    "analysis_triggers": ["*.py", "*.js", "*.sh"],
                    "commit_threshold": 10
                }
            ],
            "git_automation": {
                "enabled": True,
                "commit_message_template": "🤖 LLMdiver: {summary}\n\n{details}",
                "auto_push": False,
                "documentation_update": True,
                "branch_protection": ["main", "master"]
            },
            "llm_integration": {
                "model": "meta-llama-3.1-8b-instruct",
                "url": "http://127.0.0.1:1234/v1/chat/completions",
                "temperature": 0.3,
                "max_tokens": 4096
            },
            "repomix": {
                "style": "markdown",
                "compress": True,
                "remove_comments": True,
                "include_patterns": ["*.py", "*.js", "*.ts"],
                "ignore_patterns": ["*.md", "*.log"],
                "use_gitignore": False
            }
        }
        
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except FileNotFoundError:
            logging.warning(f"Config file not found: {self.config_path}, using defaults")
            return default_config
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in config: {e}")
            return default_config

class RepoWatcher(FileSystemEventHandler):
    def __init__(self, daemon, repo_config):
        self.daemon = daemon
        self.repo_config = repo_config
        self.last_trigger = 0
        self.debounce_time = daemon.config.config["daemon"]["watch_debounce"]
    
    def on_modified(self, event):
        if event.is_directory:
            return
        
        # Check if file matches trigger patterns
        file_path = Path(event.src_path)
        triggers = self.repo_config["analysis_triggers"]
        
        if not any(file_path.match(pattern) for pattern in triggers):
            return
            
        # Debounce rapid changes
        current_time = time.time()
        if current_time - self.last_trigger < self.debounce_time:
            return
            
        self.last_trigger = current_time
        logging.info(f"File change detected: {file_path}")
        
        # Schedule analysis
        self.daemon.schedule_analysis(self.repo_config)

class LLMStudioClient:
    def __init__(self, config):
        self.config = config
        self.url = config["llm_integration"]["url"]
        self.model = config["llm_integration"]["model"]
    
    def analyze_repo_summary(self, summary_text: str) -> str:
        """Send repo summary to LM Studio for analysis"""
        system_prompt = """You are an expert code auditor. Analyze the repository summary and identify:

1. TODO/FIXME items that need attention
2. Mock/stub implementations that should be replaced with real code
3. Dead or unused code that can be removed
4. Infinite loops or performance issues
5. Missing connections between components

Format your response as:
## Critical Issues
## TODOs and Tech Debt  
## Mock/Stub Implementations
## Dead Code Candidates
## Performance Concerns
## Architectural Improvements

Be specific and actionable in your recommendations."""

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze this repository:\n\n{summary_text}"}
            ],
            "temperature": self.config["llm_integration"]["temperature"],
            "max_tokens": self.config["llm_integration"]["max_tokens"],
            "stream": False
        }
        
        try:
            response = requests.post(self.url, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            logging.error(f"LM Studio API error: {e}")
            return f"Analysis failed: {e}"

class GitAutomation:
    def __init__(self, config):
        self.config = config
        self.git_config = config["git_automation"]
    
    def analyze_changes(self, repo_path: str) -> Dict:
        """Analyze git changes in repository"""
        try:
            repo = git.Repo(repo_path)
            
            # Get modified files
            modified_files = [item.a_path for item in repo.index.diff(None)]
            untracked_files = repo.untracked_files
            
            # Get change stats
            total_changes = len(modified_files) + len(untracked_files)
            
            return {
                "modified_files": modified_files,
                "untracked_files": list(untracked_files),
                "total_changes": total_changes,
                "repo": repo
            }
        except Exception as e:
            logging.error(f"Git analysis error: {e}")
            return {"error": str(e)}
    
    def generate_commit_message(self, analysis: str, changes: Dict) -> str:
        """Generate intelligent commit message from analysis"""
        # Extract key points from analysis
        lines = analysis.split('\n')
        critical_issues = []
        todos = []
        improvements = []
        
        current_section = ""
        for line in lines:
            line = line.strip()
            if line.startswith("## Critical Issues"):
                current_section = "critical"
            elif line.startswith("## TODO"):
                current_section = "todos"
            elif line.startswith("## Architectural"):
                current_section = "improvements"
            elif line.startswith("-") or line.startswith("*"):
                if current_section == "critical" and len(critical_issues) < 3:
                    critical_issues.append(line[1:].strip())
                elif current_section == "todos" and len(todos) < 3:
                    todos.append(line[1:].strip())
                elif current_section == "improvements" and len(improvements) < 2:
                    improvements.append(line[1:].strip())
        
        # Create summary
        summary_parts = []
        if critical_issues:
            summary_parts.append(f"Fix critical issues ({len(critical_issues)})")
        if todos:
            summary_parts.append(f"Address TODOs ({len(todos)})")
        if improvements:
            summary_parts.append(f"Implement improvements ({len(improvements)})")
        
        summary = ", ".join(summary_parts) if summary_parts else "Update codebase"
        
        # Create detailed message
        details = []
        if critical_issues:
            details.append("Critical Issues:")
            details.extend(f"- {issue}" for issue in critical_issues[:3])
        if todos:
            details.append("\nTODOs Addressed:")
            details.extend(f"- {todo}" for todo in todos[:3])
        if changes.get("modified_files"):
            details.append(f"\nModified files: {len(changes['modified_files'])}")
        if changes.get("untracked_files"):
            details.append(f"New files: {len(changes['untracked_files'])}")
        
        details_text = "\n".join(details)
        
        return self.git_config["commit_message_template"].format(
            summary=summary,
            details=details_text
        )
    
    def auto_commit(self, repo_path: str, analysis: str) -> bool:
        """Automatically commit changes with generated message"""
        try:
            changes = self.analyze_changes(repo_path)
            if changes.get("error"):
                return False
                
            if changes["total_changes"] == 0:
                logging.info("No changes to commit")
                return True
                
            repo = changes["repo"]
            
            # Stage all changes
            repo.git.add('--all')
            
            # Generate and make commit
            message = self.generate_commit_message(analysis, changes)
            repo.index.commit(message)
            
            logging.info(f"Auto-committed {changes['total_changes']} changes")
            
            # Auto-push if enabled
            if self.git_config.get("auto_push", False):
                try:
                    origin = repo.remote('origin')
                    origin.push()
                    logging.info("Auto-pushed to remote")
                except Exception as e:
                    logging.warning(f"Auto-push failed: {e}")
            
            return True
            
        except Exception as e:
            logging.error(f"Auto-commit failed: {e}")
            return False

class LLMdiverDaemon:
    def __init__(self, config_path: str = "config/llmdiver.json"):
        self.config = LLMdiverConfig(config_path)
        self.llm_client = LLMStudioClient(self.config.config)
        self.git_automation = GitAutomation(self.config.config)
        self.observers = []
        self.running = False
        self.analysis_queue = []
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_level = getattr(logging, self.config.config["daemon"]["log_level"])
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('llmdiver_daemon.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def run_repomix_analysis(self, repo_path: str) -> str:
        """Run repomix analysis on repository"""
        try:
            output_file = f"{repo_path}/.llmdiver_analysis.md"
            
            cmd = [
                "repomix", repo_path,
                "--output", output_file,
                "--style", "markdown",
                "--compress",
                "--remove-comments",
                "--include", ",".join(self.config.config["repomix"]["include_patterns"]),
                "--ignore", ",".join(self.config.config["repomix"]["ignore_patterns"])
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                with open(output_file, 'r') as f:
                    return f.read()
            else:
                logging.error(f"Repomix failed: {result.stderr}")
                return ""
                
        except Exception as e:
            logging.error(f"Repomix analysis error: {e}")
            return ""
    
    def schedule_analysis(self, repo_config: Dict):
        """Schedule repository analysis"""
        if repo_config not in self.analysis_queue:
            self.analysis_queue.append(repo_config)
            logging.info(f"Scheduled analysis for {repo_config['name']}")
    
    def process_analysis_queue(self):
        """Process queued analyses"""
        while self.running:
            if self.analysis_queue:
                repo_config = self.analysis_queue.pop(0)
                self.analyze_repository(repo_config)
            time.sleep(1)
    
    def analyze_repository(self, repo_config: Dict):
        """Analyze a repository completely"""
        logging.info(f"Starting analysis of {repo_config['name']}")
        
        try:
            # Run repomix analysis
            summary = self.run_repomix_analysis(repo_config["path"])
            if not summary:
                logging.error("Failed to generate repository summary")
                return
            
            # Send to LLM for analysis
            analysis = self.llm_client.analyze_repo_summary(summary)
            
            # Save analysis results
            analysis_dir = Path(repo_config["path"]) / ".llmdiver"
            analysis_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            analysis_file = analysis_dir / f"analysis_{timestamp}.md"
            
            with open(analysis_file, 'w') as f:
                f.write(f"# LLMdiver Analysis - {datetime.now()}\n\n")
                f.write(analysis)
            
            # Update latest analysis link
            latest_link = analysis_dir / "latest_analysis.md"
            if latest_link.exists():
                latest_link.unlink()
            latest_link.symlink_to(analysis_file.name)
            
            logging.info(f"Analysis saved to {analysis_file}")
            
            # Auto-commit if enabled
            if repo_config.get("auto_commit", False):
                self.git_automation.auto_commit(repo_config["path"], analysis)
            
        except Exception as e:
            logging.error(f"Repository analysis failed: {e}")
    
    def start_watching(self):
        """Start file system watching"""
        for repo_config in self.config.config["repositories"]:
            repo_path = repo_config["path"]
            if not os.path.exists(repo_path):
                logging.warning(f"Repository path not found: {repo_path}")
                continue
            
            observer = Observer()
            handler = RepoWatcher(self, repo_config)
            observer.schedule(handler, repo_path, recursive=True)
            observer.start()
            self.observers.append(observer)
            
            logging.info(f"Started watching {repo_config['name']} at {repo_path}")
    
    def start(self):
        """Start the daemon"""
        logging.info("Starting LLMdiver daemon...")
        self.running = True
        
        # Start file watching
        self.start_watching()
        
        # Start analysis queue processor
        analysis_thread = threading.Thread(target=self.process_analysis_queue)
        analysis_thread.daemon = True
        analysis_thread.start()
        
        # Run initial analysis on all repos
        for repo_config in self.config.config["repositories"]:
            self.schedule_analysis(repo_config)
        
        logging.info("LLMdiver daemon started successfully")
        
        # Keep daemon running
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop the daemon"""
        logging.info("Stopping LLMdiver daemon...")
        self.running = False
        
        for observer in self.observers:
            observer.stop()
            observer.join()
        
        logging.info("LLMdiver daemon stopped")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    global daemon
    if daemon:
        daemon.stop()
    sys.exit(0)

if __name__ == "__main__":
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start daemon
    daemon = LLMdiverDaemon()
    daemon.start()