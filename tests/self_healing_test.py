import os
import difflib
import sys
from groq import Groq

# 1. Setup Groq Client
client = Groq(api_key="your groq api key")

def show_diff(original, fixed):
    print("\n--- LINE-BY-LINE CHANGES (Red = Removed, Green = Added) ---")
    orig_lines = original.strip().splitlines()
    fixed_lines = fixed.strip().splitlines()
    diff = difflib.ndiff(orig_lines, fixed_lines)
    for line in diff:
        if line.startswith('+'):
            print(f"\033[92m{line}\033[0m") # Green
        elif line.startswith('-'):
            print(f"\033[91m{line}\033[0m") # Red
        elif not line.startswith('?'):
            print(line)

def test_jarvis_healing(filename):
    # Read the current content of the file
    with open(filename, "r") as f:
        buggy_code = f.read()

    print(f"--- ATTEMPTING TASK FROM {filename} ---")
    
    try:
        # Try to run the code currently in the file
        exec(buggy_code, {})
        print("STATUS: Success! No healing needed.")
    except Exception as e:
        error_info = str(e)
        print(f"STATUS: Failed! Error: {error_info}")
        
        print("\n--- JARVIS IS HEALING... ---")
        prompt = f"Fix this Python code. Return ONLY the code, no explanation.\nCode:\n{buggy_code}\nError: {error_info}"
        
        chat = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
        )
        
        fixed_code = chat.choices[0].message.content.replace("```python", "").replace("```", "").strip()
        
        # Show what is about to change
        show_diff(buggy_code, fixed_code)
        
        print("\n--- VERIFYING PATCH ---")
        try:
            # Test the patch in memory first
            exec(fixed_code, {})
            print("STATUS: Patch Verified! Saving to file...")
            
            # --- THIS LINE SAVES THE FILE ---
            with open(filename, "w") as f:
                f.write(fixed_code)
            
            print(f"SUCCESS: {filename} has been updated. Check your editor!")
        except Exception as retry_error:
            print(f"STATUS: Healing failed to verify: {retry_error}")

# --- TO TEST THIS ---
# 1. Create a file named 'task.py' in the same folder with the broken code.
# 2. Run this script.

file_to_fix = "task.py"

# Create the broken file if it doesn't exist for the demo
with open(file_to_fix, "w") as f:
    f.write("""names = []
first_name = names[0]
print(f"The first name is {first_name}")""")

test_jarvis_healing(file_to_fix)
