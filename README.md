# RegRadar

Initial setup for the RegRadar project.

## Getting started

1. Copy `.env.example` to `.env` and adjust the values if needed.
2. Start the infrastructure services:
   ```bash
   docker compose up -d
   ```
3. Create a Python virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
4. Run the sample LangGraph pipeline:
   ```bash
   python runner.py pipelines/sample.yml
   ```
