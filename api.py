import requests,json
fakka=["Fakka_2.5_Unite","Fakka_4.25_Unite","Fakka_5_Unite","Fakka_6_NewUnite","Fakka_7_Unite","Fakka_9_Unite","Fakka_10_Unite","Fakka_10_NewUnite","Fakka_10.5_Unite","Fakka_11.5_Unite","Fakka_12_Unite","Fakka_12.5_Unite","Fakka_13_Unite","Fakka_13.5_Unite","Fakka_15_Unite","Fakka_15_NewUnite","Fakka_15.5_Unite","Fakka_16.5_Unite","Fakka_17.5_Unite","Fakka_19.5_NewUnite","Fakka_20_Unite","Fakka_26_Unite"]
mared=["Mared_10_Minuts","Mared_10_Flexs","Mared_10_Social"]
all_products=fakka+mared
H={"User-Agent":"okhttp/4.12.0","Connection":"Keep-Alive","Accept-Encoding":"gzip","x-agent-operatingsystem":"16","clientId":"AnaVodafoneAndroid","Accept-Language":"ar","x-agent-device":"Samsung SM-A165F","x-agent-version":"2025.11.1","x-agent-build":"1063","digitalId":"","device-id":"b26ba335813fad21"}
def get_seamless():
    r=requests.get("http://mobile.vodafone.com.eg/checkSeamless/realms/vf-realm/protocol/openid-connect/auth",params={"client_id":"cash-app"},headers={**H,"If-Modified-Since":"Thu, 02 Apr 2026 09:09:07 GMT"})
    if r.status_code!=200:raise Exception("فشل - شغل الداتا")
    d=r.json()
    m=d.get("msisdn","")
    return d.get("seamlessToken"),"0"+m if m.startswith("1") else m
def get_token(seamless):
    r=requests.post("https://mobile.vodafone.com.eg/auth/realms/vf-realm/protocol/openid-connect/token",data={"grant_type":"password","client_secret":"b86e30a8-ae29-467a-a71f-65c73f2ff5e3","client_id":"cash-app"},headers={**H,"silentLogin":"true","CRP":"false","seamlessToken":seamless,"firstTimeLogin":"true"})
    if r.status_code!=200:raise Exception("فشل token")
    return r.json().get("access_token")
def send(token,msisdn,product,receiver,pin):
    p={"channel":{"name":"MobileApp"},"orderItem":[{"action":"insert","id":product,"product":{"characteristic":[{"name":"PaymentMethod","value":"VFCash"},{"name":"USE_EMONEY","value":"False"},{"name":"MerchantCode","value":"81841829"}],"id":product,"relatedParty":[{"id":msisdn,"name":"MSISDN","role":"Subscriber"},{"id":receiver,"name":"Receiver","role":"Receiver"}]},"@type":"Fakka_2.5_Unite","eCode":0}],"relatedParty":[{"id":pin,"name":"pin","role":"Requestor"}],"@type":"CashFakkaAndMared"}
    h={**H,"Accept":"application/json","api-host":"ProductOrderingManagement","useCase":"CashFakkaAndMared","X-Request-ID":"bb81cbe5-0c77-4673-945e-d2c0de90007a","api-version":"v2","msisdn":msisdn,"Authorization":f"Bearer {token}","Content-Type":"application/json; charset=UTF-8"}
    return requests.post("https://mobile.vodafone.com.eg/services/dxl/pom/productOrder",data=json.dumps(p),headers=h)
def check_result(resp):
    if resp.status_code in(200,201):
        try:
            d=resp.json()
            if d.get("state","").lower()=="completed":return True,"تم الشحن بنجاح"
            return False,d.get("reason","فشل")
        except:return False,"فشل قراءة الرد"
    return False,f"فشل {resp.status_code}"
