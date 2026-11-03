from dotenv import load_dotenv
from openai import OpenAI
from tools import TOOLS, run_tool
import json
import sys
import tools
from pathlib import Path

tools.workspace = Path(sys.argv[1]).resolve()
tools.workspace.mkdir(parents=True, exist_ok=True)

load_dotenv()
client = OpenAI()

MODEL = "gpt-5-mini"
MAX_STEPS = 40

INSTRUCTIONS = """You are a coding agent working inside a workspace folder.
All file paths are relative to that folder. Never include the word 'workspace' in a path.
Use python3, never python.

When building an app:
1. First write a short plan: which files you will create.
2. Create the files with write_file. Use edit_file for small changes later.
3. At the end, re-read your files once and check for mistakes (wrong ids, missing tags, wrong file names).
4. Never start a server unless the user asks for one. If you start one, stop it before finishing.

Unless the user names a tech stack, build plain HTML, CSS and JavaScript with no server and no build step.
Use the files index.html, style.css and app.js.

Design rules for any UI you build:
- Clean, modern look: a centered card on a soft background, generous spacing, rounded corners, a subtle shadow.
- One accent color plus grays. Use a system font stack.
- Every button and input has hover and focus styles, with a small transition (about 0.2s).
- Works on phone screens: include the viewport meta tag and a responsive layout.
- Save data in localStorage so it survives a page refresh.
- Show a friendly message when the list is empty.

To run tests, use: python3 -m pytest -q
Fix bugs in the source file, never by editing the tests to pass.
Do not claim success unless you actually checked it."""

chat = []   

try:
    while True:
        try:
            user_message = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if user_message in ("exit", "quit"):
            break
        if not user_message:
            continue

        chat.append({"role": "user", "content": user_message})

        for step in range(MAX_STEPS):
            print(f" step {step}")
            response = client.responses.create(
                model=MODEL, input=chat, tools=TOOLS, instructions=INSTRUCTIONS
            )
            chat.extend(response.output)

            asked_for_tool = False
            for item in response.output:
                if item.type == "function_call":
                    asked_for_tool = True
                    args = json.loads(item.arguments)
                    result = run_tool(item.name, args)
                    print(f"  -> {item.name} {args}")
                    print(f"  <- {result[:300]}")
                    chat.append({
                        "type": "function_call_output",
                        "call_id": item.call_id,
                        "output": result,
                    })

            if not asked_for_tool:
                print(response.output_text)
                break
        else:
            print("Stopped: hit MAX_STEPS without finishing.")
finally:
    tools.stop_server()