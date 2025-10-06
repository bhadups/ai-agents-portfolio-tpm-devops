Action Item Extractor Agent
Overview

The Action Item Extractor Agent is an autonomous Python agent designed to process meeting notes and extract actionable items in a structured format. Using OpenAI’s GPT API, it identifies tasks, assigns owners, and detects deadlines where applicable.

This agent can run in two modes:

Scheduled / periodic: Run after meetings or daily to process collected notes.

Event-driven: Trigger automatically when new meeting notes are uploaded to a centralized location.

Centralized Input Storage

All meeting notes are stored centrally, for example in a GCP Storage Bucket or shared folder:

gs://<your-bucket-name>/meeting-notes/
    ├── raw_notes/
    └── processed_action_items/


The agent reads the notes from this location.

Extracted action items are saved as CSV and optionally emailed to stakeholders.

Benefits:

Centralized access for multiple agents or teams.

Historical tracking of tasks.

Auditing and reporting made easier.

Requirements

Python >= 3.10 and the following packages:

pandas
openai
python-dateutil
tabulate


Install dependencies in a virtual environment:

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

Environment Variables

The agent requires your OpenAI API key:

export OPENAI_API_KEY="sk-xxxxxx"


Or use a .env file with python-dotenv:

OPENAI_API_KEY=sk-xxxxxx

Directory Structure
action-item-extractor/
├── agent.py                # Main agent script
├── requirements.txt
├── sample_input.txt        # Example meeting notes
├── action_items.csv        # Output file (generated)
└── .env                    # Optional environment variables

Running the Agent
python agent.py sample_input.txt


Output CSV is saved to action_items.csv.

A Markdown table of extracted action items is printed to the terminal.

Notifications

The agent can be extended to send email notifications:

CSV attachment with extracted action items

Markdown table in the email body

Example subject line: Meeting Action Items – 2025-10-06

Deployment / Automation

Scheduled execution: Use cron or Task Scheduler to run the agent after each meeting or daily.

Event-driven execution: Use GCP Cloud Functions or AWS Lambda to trigger the agent when new meeting notes are uploaded.

Next Steps / Enhancements

Integrate with Slack, Teams, or email notifications for real-time visibility.

Store extracted action items in a central database for auditing and reporting.

Combine with other agents (SQL tuning, DevOps metrics) into a unified orchestrator.
