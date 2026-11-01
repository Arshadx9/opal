from pathlib import Path
import subprocess
import os
import signal

server = None
server_log=None



workspace = Path(__file__).parent /"workspace"
MAX_OUTPUT = 4000



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
   
},
{
        "type": "function",
    "name": "edit_file",
    "description": "Replace one exact piece of text in an existing file. old_text must match exactly one place in the file.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "path relative to the workspace folder"},
            "old_text": {"type": "string", "description": "the exact text to replace"},
            "new_text": {"type": "string", "description": "the text to put in its place"},
        },
        "required": ["path", "old_text", "new_text"],
    },
},
{

    "type": "function",
    "name": "start_server",
    "description": "Start a long-running command (like a web server) in the background. Returns immediately. Output goes to server.log.",
    "parameters": {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "the command that starts the server"},
        },
        "required": ["command"],
    }
},
{
    "type": "function",
    "name": "stop_server",
    "description": "Stop the server started with start_server.",
    "parameters": {"type": "object", "properties": {}},
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
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(text)
    return "ok"


def edit_file(path , old_text ,new_text):
    full_path = safe_path(path)
    if full_path is None:
        return "Error : Path is not in Workspace"
    readcontent = full_path.read_text()
    contentcount = readcontent.count(old_text)

    if contentcount == 0:
        return f"Error: old_text was not found in {path}. It must match the file exactly ,including whitespace and indentation. Use read_file to see the current contents, then try again."
    if contentcount > 1:
        return f"Error: old_text appears {contentcount} times in {path}, so it's unclear which one to change. Include more surrounding lines in old_text so it matches exactly one place."

    new_content = readcontent.replace(old_text , new_text)

    full_path.write_text(new_content)
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
    output = result.stdout + result.stderr          

    if len(output) > MAX_OUTPUT:                   
        half = MAX_OUTPUT // 2
        cut = len(output) - MAX_OUTPUT
        output = output[:half] + f"\n[... {cut} characters cut ...]\n" + output[-half:]

    return f"exit code: {result.returncode}\n{output}"   


def start_server(command):
    global server , server_log
    if server not in None:
        return "Error: server is already running, call stop_server first"

    server_log = open(workspace / "server_log" , "w")
    server = subprocess.Popen(
        command,
        shell= True,
        cwd = workspace,
        stdout=server_log,
        stderr=server_log,
        start_new_session=True
    )
    return "server started it's output is being written to server_log file"


def stop_server():
    global server , server_log
    if server is None:
        return "no server is running"

    try:
        os.killpg(server.pid , signal.SIGTERM)
    except ProcessLookupError:
        pass


    try:
        server.wait(timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(server.pid , signal.SIGKILL)
        server.wait()

    server_log.close()
    server = None
    server_log = None
    return "server stopped"

def run_tool(name , args):

  try:
    if name == "read_file":
        return read_file(args["path"])
    if name =="write_file":
        return write_file(args["path"] , args["text"])
    if name == "run_command":
        return run_command(args["command"])
    if name == "edit_file":
        return edit_file(args["path"] , args["old_text"] , args["new_text"])
    if name == "start_server":
        return start_server(args["command"])
    if name == "stop_server":
        return stop_server()
    return "Error : tool does not exist"
  except Exception as e:
      return f"Error : {e}"
      