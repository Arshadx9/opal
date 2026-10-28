from pathlib import Path
import subprocess

workspace = Path(__file__).parent /"workspace"



TOOLS = [
{
"type" : "function",    
"name"  :"read_file",
"description" : "read the file's content",
"parameters" : {
    "type":"object", 
     "properties" : {
         "path" : {
             "type": "string",
             "description" : "path relative to the workspace folder, for example 'utils.py' or 'src/utils.py'. Do not include the word 'workspace' in the path."
         },
        },
  "required" : ["path"]

}
},
{
    "type": "function",
    "name": "write_file",
    "description": "Write text to a file in the workspace. Replaces the whole file if it already exists.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "path relative to the workspace folder, for example 'utils.py' or 'src/utils.py'. Do not include the word 'workspace' in the path.",
            },
            "text": {
                "type": "string",
                "description": "the full text to write into the file",
            },
        },
        "required": ["path", "text"],
    },
},
{
    "type":"function",
    "name":"run_command",
    "description":"use this function to run any commands",
    "parameters":{
        "type":"object",
        "properties":{
            "command":{
                "type":"string",
                "description":"this is the command that needs to be executed"
            }
        },
    "required":["command"]
    }
   
}
]

def safe_path(path):
    full_path = (workspace / path).resolve()
    if not full_path.is_relative_to(workspace.resolve()):
        return None 
    return full_path
    

def read_file(path):
    modelaskedthis = (workspace/path).resolve()
    if not  modelaskedthis.is_relative_to(workspace.resolve()):
        return "Error : Path is outside workspace"
    return modelaskedthis.read_text()


def write_file(path , text): 
    full_path = safe_path(path)
    if full_path is None:
        return "Error : Path is not in workspace"
    full_path.write_text(text)
    return "ok"


def run_command(command):
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=workspace,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        return "Error : command took longer than 60 seconds and was stopped"
    return result.stdout + result.stderr  


def run_tool(name , args):

  try:
    if name == "read_file":
        return read_file(args["path"])
    if name =="write_file":
        return write_file(args["path"] , args["text"])
    if name == "run_command":
        return run_command(args["command"])
    return "Error : tool does not exist"
  except Exception as e:
      return f"Error : {e}"
      