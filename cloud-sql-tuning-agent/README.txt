Cloud SQL Tuning Agent
Overview

The Cloud SQL Tuning Agent is an autonomous Python agent designed to analyze Cloud SQL logs and metrics, identify performance bottlenecks, and generate actionable recommendations. The agent leverages OpenAI’s GPT API to provide intelligent analysis and can output results in CSV format or as email notifications.

This agent can run in two modes:

Scheduled / periodic: Run at regular intervals (e.g., nightly) to process logs.

Event-driven: Trigger automatically when new logs or metrics are uploaded to a centralized storage location.

Centralized Logging Architecture

All Cloud SQL logs, metrics, and flags are stored centrally in a GCP Storage Bucket:

gs://<your-bucket-name>/cloudsql-logs/
    ├── slow_queries/
    ├── metrics/
    └── db_flags/


The agent reads the logs from this bucket (or local copies synced from it).

Output recommendations can also be stored back in the bucket or emailed to stakeholders.

This approach ensures:

Historical analysis is possible.

Multiple agents or teams can access the same data.

Auditing and compliance are simplified.

Requirements

Python >= 3.10 and the following packages:

pandas
openai
python-dateutil
sqlparse
psycopg2-binary
mysql-connector-python
tabulate


Install dependencies in a virtual environment:

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

Environment Variables

The agent requires your OpenAI API key. You can set it as an environment variable:

export OPENAI_API_KEY="sk-xxxxxx"


Or use a .env file with python-dotenv:

OPENAI_API_KEY=sk-xxxxxx

Directory Structure
cloud-sql-tuning-agent/
├── agent.py                # Main agent script
├── requirements.txt
├── sample_inputs/          # Example input files
│   ├── metrics.json
│   ├── db_flags.txt
│   └── slow_queries.log
├── outputs/                # Generated recommendations CSV
└── .env                    # Optional environment variables

Running the Agent
python agent.py sample_inputs/metrics.json sample_inputs/db_flags.txt sample_inputs/slow_queries.log


Output CSV is saved to outputs/recommendations.csv.

A Markdown table of recommendations is printed to the terminal.

Notifications

The agent can be extended to send email notifications using SMTP, SendGrid, or other services:

CSV attachment with recommendations

Markdown table in the email body

Subject line example: Cloud SQL Tuning Recommendations – 2025-10-06

Deployment / Automation

Scheduled execution: Use cron or Task Scheduler to run the agent at regular intervals.

Event-driven execution: Use GCP Cloud Functions or AWS Lambda to trigger the agent when new logs are uploaded to the storage bucket.

Next Steps / Enhancements

Integrate multiple agents (SQL tuning, DevOps metrics, etc.) into a central orchestrator.

Add Slack or Teams notifications for immediate visibility.

Store all output recommendations in a central database for auditing and analytics.
