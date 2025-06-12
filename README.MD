README.md - Project Overview
Project Name: greenantix-gmailspambot

This project is a sophisticated, dual-LLM Gmail automation suite designed to intelligently clean, categorize, and manage large volumes of email. It operates in multiple modes: as an interactive GUI application for direct user control, a powerful command-line tool for bulk processing, and as a fully autonomous, scheduled background service.

Core Architectural Pillars:
Modular Design: The system is broken into logical components:

API Utilities (gmail_api_utils.py): A robust, reusable wrapper for all Gmail API interactions, featuring batch operations and exponential backoff for resilience.
LLM Integration (gmail_lm_cleaner.py): Supports both local models via LM Studio and cloud models via the Gemini API, allowing for flexible and powerful email analysis.
Scheduling (cron_utils.py): A persistent, cron-based scheduler for managing autonomous jobs like analysis and cleanup.
Error Handling (exceptions.py): A dedicated module for custom, specific exceptions, enabling intelligent recovery from failures.
Multiple Operation Modes:

GUI Mode (gmail_lm_cleaner.py): A Tkinter-based graphical interface for interactive processing, settings management, and viewing analytics.
Bulk Processing Mode (bulk_processor.py): A command-line tool designed to handle massive backlogs (75k+ emails) by employing an intelligent "filter-first" strategy, analyzing high-volume senders before falling back on AI for the remainder.
Autonomous Mode (autonomous_runner.py): A long-running service that executes scheduled jobs for real-time processing of new emails, batch analysis with Gemini, and periodic cleanup, designed for deployment with systemd.
Intelligence and Learning:

Dual-LLM Strategy: Uses a local LLM (e.g., via LM Studio) for real-time, privacy-focused analysis and a powerful cloud LLM (Gemini) for deeper, periodic batch analysis to generate new rules.

Email Learning Engine (EmailLearningEngine): A framework designed to log categorization decisions and user feedback, with the goal of suggesting rule improvements and detecting new email patterns over time. (Note: This is currently a key area for development).

ARCHITECTURE.md - System Architecture
1. Core Components
gmail_lm_cleaner.py: The central nervous system.

GmailCleanerGUI: The Tkinter front-end. It launches processing tasks in background threads to keep the UI from freezing.
GmailLMCleaner: The main class holding the core business logic. It authenticates, fetches emails, builds prompts, calls LLMs, and executes actions.
EmailLearningEngine: A class designed to track decisions and learn from them. It logs actions to logs/categorization_history.json.
gmail_api_utils.py: The API Abstraction Layer.

get_gmail_service(): Handles the entire OAuth2 flow, creating or refreshing token.json as needed.
GmailLabelManager & GmailEmailManager: Classes that encapsulate all label and message operations (create, list, modify, batch delete, etc.), abstracting the raw API calls away from the main logic.

exponential_backoff_retry(): A crucial decorator that wraps API calls to handle rate limiting and transient network errors gracefully.
2. Autonomous Operation Subsystem
autonomous_runner.py: The daemon process.

It uses cron_utils.CronScheduler to manage a schedule of jobs (e.g., realtime_processing, batch_analysis, email_cleanup).
It checks prerequisites before running a job (e.g., is the Gemini API key present?).
It wraps job execution in robust try...except blocks, using custom exceptions from exceptions.py to handle errors intelligently (e.g., waiting longer on an authentication failure vs. a recoverable API error).
cron_utils.py: The Scheduler.

Manages multiple jobs with standard cron expressions.
Persists the state of each job (last run time, status) to data/automation_state.json, ensuring that if the runner restarts, it knows which jobs were missed and are due.
health_check.py: The Monitoring Service.

A Flask-based microservice that exposes /health and /status endpoints. This allows external monitoring tools to check if the bot is alive and see the status of its scheduled jobs.
3. Data and Rules Management
config/: Holds static configuration like priority_patterns.json.
rules/: Contains dynamic, per-category filtering rules (e.g., BILLS.json, SHOPPING.json). These files are intended to be modified by the system as it learns.
logs/: Stores operational logs (automation.log, bulk_processing.log) and the critical categorization_history.json for the learning engine.
data/: Holds persistent state files, most importantly automation_state.json for the cron scheduler.
The Path Forward: A Detailed Progression Plan
This plan is structured into phases, starting with critical bug fixes and stabilization, moving to feature completion, and finally to refinement and hardening.

ROADMAP.md - High-Level Progression
Phase 1: Critical Stability & Reliability.

Objective: Fix the core bugs that cause crashes and incomplete processing. Make the application reliable enough for extended use.
Key Tasks: Fix the pagination loop, implement robust UI error feedback, complete the filter-harvesting logic.
Phase 2: The Intelligence Layer.

Objective: Transition the EmailLearningEngine from a placeholder to a functional system. Fulfill the "intelligent" promise of the application.
Key Tasks: Implement rule suggestion logic, enable the "Apply Suggestions" feature, and connect the Analytics dashboard to real data.
Phase 3: Feature Completion & Usability.

Objective: Complete all user-facing features and improve the user experience, including the "ugly UI."
Key Tasks: Implement the unsubscribe action, make the rule editor fully functional, and add better UI feedback mechanisms.
Phase 4: Hardening & Deployment.

Objective: Prepare the application for autonomous, long-term deployment.
Key Tasks: Conduct "chaos testing," perform extended-duration autonomous runs, and finalize all documentation for end-users and developers.
