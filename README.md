# AI Incremental GitHub Publisher

An autonomous, local automation system that gradually publishes an existing local software project to GitHub in small, logically coherent daily releases. It uses AI to analyze your repository, build a feature dependency graph, split large tasks, and automatically generate and execute a daily release roadmap.

## Prerequisites

- **Python 3.9+**
- **Git** (installed and configured with your user/email)
- **A Google Gemini API Key** (Get one from [Google AI Studio](https://aistudio.google.com/app/apikey))

## Setup Instructions

### 1. Clone or Copy the Tool
Ensure the publisher code (`src/`, `tests/`, `requirements.txt`, etc.) is located in the root of the project you want to incrementally publish, or in a directory accessible to your terminal.

### 2. Install Dependencies
Open your terminal (PowerShell or Command Prompt) and install the required Python packages:
```bash
pip install -r requirements.txt
```

### 3. Set your Gemini API Key
The AI needs an API key to perform architecture analysis and intelligent code diff checks.
Set it as an environment variable in your terminal session:

**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="your_api_key_here"
```

**Windows (CMD):**
```cmd
set GEMINI_API_KEY=your_api_key_here
```

*(Note: You must set this variable in the terminal session before running the publisher. Alternatively, you can add it permanently to your Windows System Environment Variables).*

---

## Usage Guide

The tool provides a unified CLI via `main.py`.

### Step 1: Initialize the Roadmap
Run the `init` command in your project root. 
*This will analyze your local files, identify features, determine dependencies, and generate a step-by-step release roadmap. It creates a `.incremental-publisher/` folder to store state.*
```bash
python src/cli/main.py init
```

### Step 2: Review the Plan
You can view the AI-generated roadmap anytime:
```bash
python src/cli/main.py plan
```

### Step 3: Test a Release (Dry Run)
Before actually committing and pushing, perform a dry run. The tool will check for unrelated changes, validate the code (if tests exist), and show you the exact diff it intends to commit.
```bash
python src/cli/main.py release --dry-run
```

### Step 4: Schedule Daily Publishing
To let the system run automatically in the background, configure the Windows Task Scheduler through the CLI. For example, to run every day at 9:00 AM:
```bash
python src/cli/main.py schedule --time 09:00
```
*The system is idempotent and handles crash recovery; if your laptop is offline at 9:00 AM, it will catch up on its next execution.*

---

## Additional Commands

- **Check System Health:**
  ```bash
  python src/cli/main.py doctor
  ```
- **Check Project Status & Next Release:**
  ```bash
  python src/cli/main.py status
  python src/cli/main.py next
  ```
- **View Past Releases:**
  ```bash
  python src/cli/main.py history
  ```
- **Re-analyze Features without changing the roadmap:**
  ```bash
  python src/cli/main.py analyze
  ```
- **Reset the Publisher State (Danger):**
  *Removes the `.incremental-publisher` folder but does NOT touch your source code or Git history.*
  ```bash
  python src/cli/main.py reset-state
  ```

## Security Note
This tool treats your local repository as sensitive. It is hardcoded to automatically exclude common secrets (like `.env`, `.pem`, `credentials`) and uses regex scanning to ensure API keys (AWS, GCP, generic tokens) in your code are never sent to the LLM during architecture analysis.
