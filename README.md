# Gmail Intelligent Cleaner

A smart Gmail management tool with a Tkinter GUI that uses a local LLM (via LM Studio) to intelligently sort, process, and clean your inbox. It is designed with a "human-in-the-loop" philosophy, where automated tools handle the bulk work and the user makes the final decisions.

## 🚀 Quick Start for Linux

### 1. Simple Startup
```bash
chmod +x start.sh
./start.sh
```

### 2. Simple Shutdown
```bash
chmod +x stop.sh
./stop.sh
```

The startup script handles environment setup, dependency installation, and launches the main application.

## 📋 Core Requirements

1.  **Python 3.8+**: Ensure you have a modern version of Python installed.
2.  **Gmail API Credentials**:
    *   Go to the [Google Cloud Console](https://console.cloud.google.com/apis/credentials).
    *   Create or use an existing project.
    *   Enable the **Gmail API**.
    *   Create an "OAuth client ID" credential for a "Desktop app".
    *   Download the credentials JSON file and save it as `config/credentials.json`.
3.  **LM Studio (Recommended)**:
    *   Download from the [LM Studio website](https://lmstudio.ai/).
    *   Download the **Llama-3.1-8B-Instruct** model (or another compatible model).
    *   Start the local server on the default port (1234).

## 🏛️ System Architecture

This system employs a multi-stage processing pipeline designed for safety, efficiency, and accuracy.

### 1. Tiered Importance System

Emails are categorized into a tiered system to ensure critical messages are never mishandled:

*   **PRIORITY**: The highest tier. Reserved for emails from explicitly defined important senders like financial institutions (banks), real estate (Zillow), and development platforms (GitHub). These are identified using patterns in `config/priority_patterns.json`.
*   **INBOX**: Standard inbox messages that are not otherwise categorized. These are the primary candidates for LLM analysis.
*   **Other Categories**: Includes standard Gmail categories like `SOCIAL`, `PROMOTIONS`, `UPDATES`, and `FORUMS`.

### 2. Filter-First Processing Strategy

Before any LLM analysis occurs, the system applies a "filter-first" strategy:

1.  **Filter Harvesting**: The `tools/filter_harvester.py` module extracts all existing Gmail filters from your account.
2.  **Query Conversion**: It converts the filter criteria (e.g., from, subject, has words) into standard Gmail search queries.
3.  **Action Emulation**: The system can then use these queries to emulate your manual sorting rules, providing a baseline for automated processing and reducing the workload on the LLM.

This ensures that the system respects your existing organizational structure before applying its own logic.

## ✨ Features

-   **Intelligent Sorting**: Uses a local LLM to understand email content and context.
-   **Memory-Efficient Backlog Analysis**: The `tools/backlog_analyzer.py` can process 75,000+ emails to find patterns without high memory usage.
-   **Configurable & Extendable**: All settings, rules, and patterns are stored in JSON files in the `config/` directory.
-   **Safe Mode**: A "dry run" option lets you preview actions before they are executed.
-   **GUI Interface**: A simple Tkinter GUI for managing the process.
-   **Conservative by Default**: The system is designed to be cautious and avoid deleting potentially important emails.

## 🔒 OAuth Scope Requirements

The application requires the following OAuth scopes. You will be prompted to grant these permissions on the first run.

-   `https://www.googleapis.com/auth/gmail.modify`: Allows the application to read, modify, and move emails (e.g., add/remove labels, trash).
-   `https://www.googleapis.com/auth/gmail.settings.basic`: Allows reading of user settings, specifically for fetching Gmail filters.

If you change the scopes, you must delete the `config/token.json` file to re-authenticate.

## 📁 Project Structure

-   `gmail_lm_cleaner.py`: The main application logic and GUI.
-   `gmail_api_utils.py`: Reusable utilities for interacting with the Gmail API.
-   `tools/`: Contains supporting modules for advanced processing.
    -   `filter_harvester.py`: Extracts and parses existing Gmail filters.
    -   `backlog_analyzer.py`: Analyzes large email backlogs for patterns.
-   `config/`: Houses all configuration files.
    -   `settings.json`: General application settings.
    -   `credentials.json`: Your downloaded Google Cloud OAuth credentials.
    -   `token.json`: The generated OAuth token (do not share this).
    -   `priority_patterns.json`: Defines patterns for the `PRIORITY` category.
-   `logs/`: Contains application logs for debugging.
-   `rules/`: (Legacy) Contains JSON-based filtering rules.

## 🆘 Troubleshooting

**"Credentials not found"**
- Ensure your `credentials.json` file is located in the `config/` directory.

**"LM Studio not running"**
- The application can run without an LLM, but its analytical capabilities will be limited. For full functionality, ensure LM Studio is running with a model loaded.

**"Python package errors"**
- The `start.sh` script attempts to install dependencies from `requirements.txt`. If it fails, you can install them manually:
  ```bash
  pip install -r requirements.txt
  ```

## 🛡️ Privacy & Security

-   **Local First**: All processing, including LLM analysis, happens locally on your machine.
-   **No Data Sharing**: Your emails and authentication tokens are never sent to any third-party servers (other than Google's own API servers).
-   **Secure Token Storage**: The `token.json` is stored locally in the `config/` directory and should be treated like a password.