import requests,random,string
from datetime import datetime
URL="https://vfcash-f49e3-default-rtdb.firebaseio.com"

def gen_code(n=8):
    return "".join(random.choices(string.ascii_uppercase+string.digits,k=n))

def check_code(code):
    r=requests.get(f"{URL}/codes/{code}.json")
    if r.status_code==200 and r.json():
        d=r.json()
        if not d.get("used",False):
            return True,d.get("type","user")
    return False,None

def use_code(code):
    requests.patch(f"{URL}/codes/{code}.json",json={"used":True,"at":str(datetime.now())})

def add_code(code,t="user"):
    requests.put(f"{URL}/codes/{code}.json",json={"used":False,"type":t,"at":str(datetime.now())})

def log_op(msisdn,product,receiver,status,code):
    requests.post(f"{URL}/logs.json",json={"msisdn":msisdn,"product":product,"receiver":receiver,"status":status,"code":code,"time":str(datetime.now())})

def get_logs():
    r=requests.get(f"{URL}/logs.json")
    if r.status_code==200 and r.json():return r.json()
    return {}
