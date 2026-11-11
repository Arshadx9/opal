from pathlib import Path
import uuid
import os
import json 


sessions_dir = Path(__file__).parent / "sessions"
sessions_dir.mkdir(exist_ok=True)

diary_path = sessions_dir / f"{uuid.uuid4().hex}.jsonl"
last_event_id = None

def save_event(event_type , data):
    global last_event_id

    event_id = uuid.uuid4().hex
    event = {
        "version" : 1,
        "id" :event_id ,
        "parent_id":last_event_id,
        "type":event_type,
        "data":data
    }

    with diary_path.open("a" , encoding="utf-8") as file:
        file.write(json.dumps(event)+ "\n")
        file.flush()
        os.fsync(file.fileno())

    last_event_id = event_id

def load_event(path):
    events= []
    with Path(path).open("rb") as file:
        for line in file:
            if not line.endswith(b"\n"):
                break
            if line.strip():
                events.append(json.loads(line.decode("utf-8")))
    return events

    