import sys
import pandas as pd

# Minimal parser for current use
def extract_actions_basic(meeting_notes):
    actions = []
    for line in meeting_notes.split('\n'):
        line = line.strip()
        if line.startswith('-'):
            actions.append(line[1:].strip())
    return actions

# Placeholder for GPT/AI integration
def extract_actions_gpt(meeting_notes):
    """
    TODO: Replace with actual GPT/AI call.
    Example:
        import openai
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": meeting_notes}]
        )
        return parsed_actions_from_response(response)
    """
    # For now, fallback to basic parser
    return extract_actions_basic(meeting_notes)

if __name__ == "__main__":
    input_file = sys.argv[1]
    with open(input_file, 'r') as f:
        notes = f.read()

    # Use GPT placeholder (currently falls back to basic parser)
    actions = extract_actions_gpt(notes)

    # Save actions to CSV
    df = pd.DataFrame(actions, columns=["Action Item"])
    df.to_csv("action_items.csv", index=False)
    
    # Print to terminal
    print("\nExtracted Action Items:")
    print(df)
    print("\nSaved to action_items.csv")

