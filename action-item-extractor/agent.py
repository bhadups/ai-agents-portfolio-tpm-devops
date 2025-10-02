import sys
import pandas as pd
import openai

# Make sure you have your OpenAI API key set as an environment variable:
# export OPENAI_API_KEY="your_api_key"

def extract_actions_gpt(notes):
    """
    Uses GPT to extract structured action items from meeting notes.
    Returns a list of dictionaries: {"Action Item": ..., "Owner": ..., "Deadline": ...}
    """
    prompt = f"""
    Extract all actionable tasks from the following meeting notes.
    Return the output in JSON format as a list of objects with keys: Action Item, Owner, Deadline.
    If a task does not have an owner or deadline, leave it empty.

    Meeting Notes:
    {notes}
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    # Extract text from GPT response
    text_output = response['choices'][0]['message']['content']

    # Parse JSON output
    import json
    try:
        actions = json.loads(text_output)
    except json.JSONDecodeError:
        # Fallback if GPT returns invalid JSON
        print("Warning: GPT output could not be parsed as JSON. Using empty list.")
        actions = []

    return actions

if __name__ == "__main__":
    input_file = sys.argv[1]
    with open(input_file, 'r') as f:
        notes = f.read()

    actions = extract_actions_gpt(notes)

    if not actions:
        print("No actions extracted. Please check GPT output.")

    # Save actions to CSV
    df = pd.DataFrame(actions)
    df.to_csv("action_items.csv", index=False)

    # Print nicely
    print("\nExtracted Action Items:")
    print(df)
    print("\nSaved to action_items.csv")

