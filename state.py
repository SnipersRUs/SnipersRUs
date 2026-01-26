import json, os, datetime as dt

STATE_PATH = "state.json"

def load_state():
    if not os.path.exists(STATE_PATH):
        return {}
    with open(STATE_PATH,"r") as f:
        try:
            return json.load(f)
        except:
            return {}

def save_state(s):
    with open(STATE_PATH,"w") as f:
        json.dump(s, f, indent=2)

def day_key(d=None):
    d = d or dt.date.today()
    return d.isoformat()

def week_key(d=None):
    d = d or dt.date.today()
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"
