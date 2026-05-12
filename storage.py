import json,os
F=os.path.expanduser("~/.vcash.json")
def save(d):
    open(F,"w").write(json.dumps(d))
def load():
    if not os.path.exists(F):return {}
    return json.load(open(F))
def clear():
    if os.path.exists(F):os.remove(F)
