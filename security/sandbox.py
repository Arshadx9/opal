import os
import subprocess
import sys
import tempfile
from pathlib import Path


TMP = Path(tempfile.gettempdir()).resolve()

SAFE_ENV = ("PATH" , "HOME" , "USER" , "LANG" ,"TERM" , "TMPDIR")

SECRETS = r'(regex #"/\.env[^/]*$")'

def profile(workspace):
    """The Seatbelt rules for one workspace. Last matching rule wins."""
    return f"""(version 1)
(deny default)
(allow process-exec process-fork)
(allow signal (target same-sandbox))
(allow sysctl-read)
(allow file-read*)
(deny file-read* {SECRETS})
(allow file-write* (subpath "{workspace}") (subpath "{TMP}") (literal "/dev/null"))
(deny file-write* {SECRETS})
(deny network*)
"""

def run (command , workspace, timeout = 60):
    if sys.platform != "darwin":
        raise RuntimeError("no sandbox on this OS, refusing to run commands")
    env = {key: os.environ[key] for key in SAFE_ENV if key in os.environ}
    return subprocess.run(
        ["sandbox-exec" , "-p" , profile(workspace) , "/bin/sh", "-c" , command] , 
        cwd = workspace, 
        env =env , 
        capture_output= True, 
        text = True, 
        timeout=timeout,
    )
