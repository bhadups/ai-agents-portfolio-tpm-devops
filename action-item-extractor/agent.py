import sys
import pandas as pd
import re

# Minimal parser fallback
def extract_actions_basic(notes):
    actions = []
    for line in notes.split('\n'):
        line = line.strip()
        if line.startswith('-'):
            actions.append({"Action Item": line[1:].strip(), "Owner": "", "Deadline": ""})
    return actions

# GPT/AI placeholder parser
def extract_actions_gpt(notes):
    """
    TODO: Replace this with actual GPT/OpenAI call for AI parsing.
    Example:
        import openai
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": notes}]
        )
        # Parse response to extract structured items
        return parsed_actions
    For now, we simulate AI by using regex to detect sentences that look like action items.
    """
    actions = []

    # Simple regex-based simulation: capture sentences with verbs like 'needs', 'should', 'will', 'to'
    sentences = re.split(r'\.\s+', notes)
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        if re.search(r'\b(needs|should|will|to)\b', s, re.IGNORECASE):
            # Attempt to find owner (first capitalized word at start)
            owner_match = re.match(r'^([A-Z][a-z]+)', s)
            owner = owner_match.group(1) if owner_match else ""
            # Attempt to find a simple deadline (keywords like Monday, Friday, dates

