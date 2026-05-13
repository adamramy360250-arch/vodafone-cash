import json,os
F=os.path.expanduser("~/.vcash.json")
def save(seamless,token,msisdn):
    d={}
    if os.path.exists(F):
        try:d=json.load(open(F))
        except:d={}
    d["seamless"]=seamless
    d["token"]=token
    d["msisdn"]=msisdn
    open(F,"w").write(json.dumps(d))
def load():
    if not os.path.exists(F):return {}
    try:return json.load(open(F))
    except:return {}
def clear():
    if os.path.exists(F):os.remove(F)
