from dotenv import load_dotenv
from openai import OpenAI
from tools import TOOLS , run_tool
import json
import sys
import tools
from pathlib import Path


tools.workspace = Path(sys.argv[2]).resolve()

load_dotenv()
client = OpenAI()

MODEL = "gpt-5-mini"
MAX_STEPS = 20

chat = [{
       "role" :"user" , 
        "content":sys.argv[1]
}]

INSTRUCTIONS = """You are a coding agent working inside a workspace folder.
All file paths are relative to that folder. Never include the word 'workspace' in a path.
To run tests, use: python3 -m pytest -q
Use python3, never python.
Fix bugs in the source file, never by editing the tests to pass.
Do not claim success unless the tests actually passed."""


while True:
    try:
        user_message = input("\n> ").strip()
    except (EOFError ,KeyboardInterrupt):
        break
    if user_message in ("exit" , "quit"):
        break
    if not user_message:
        continue

    chat.append({"role": "user", "content": user_message})


 

    for step in range(MAX_STEPS):
        print(f" step {step}")
        response = client.responses.create(model= MODEL, input=chat , tools=TOOLS ,instructions=INSTRUCTIONS)
        chat.extend(response.output)


    asked_for_tool = False



    for item in response.output:
        if item.type == "function_call":
            asked_for_tool = True
            args = json.loads(item.arguments)
            result = run_tool(item.name , args)
            print(f"  -> {item.name} {args}")
            print(f"  <- {result[:300]}")
            chat.append({
                "type" :"function_call_output",
                "call_id": item.call_id,
                 "output" : result
                })
        
    if not asked_for_tool:
        print(response.output_text)
        break
        
        
   







