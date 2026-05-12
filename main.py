import os,json,threading
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager,Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.core.window import Window
from api import all_products,get_seamless,get_token,send,check_result
from storage import save,load,clear
from firebase import check_code,use_code,add_code,gen_code,log_op,get_logs

Window.clearcolor=(0.05,0.03,0,1)
G=(1,0.85,0.2,1)
D=(0.8,0.53,0,1)
R=(0.8,0.1,0.1,1)
GR=(0.1,0.7,0.1,1)

def btn(text,color=None,h=50):
    b=Button(text=text,font_size=16,size_hint_y=None,height=h,background_color=color or D,background_normal="",bold=True)
    return b

def lbl(text,size=15,color=None,h=35):
    l=Label(text=text,font_size=size,size_hint_y=None,height=h,color=color or G,halign="center",valign="middle")
    l.bind(size=l.setter("text_size"))
    return l

def inp(hint,pw=False,h=45):
    return TextInput(hint_text=hint,font_size=15,size_hint_y=None,height=h,multiline=False,password=pw,background_color=(0.1,0.06,0,1),foreground_color=G,hint_text_color=(0.5,0.4,0,1),cursor_color=G,padding=[10,10])

class SplashScreen(Screen):
    def __init__(self,**kw):
        super().__init__(**kw)
        l=BoxLayout(orientation="vertical",padding=[25,50,25,30],spacing=12)
        l.add_widget(lbl("المطور",13,(0.7,0.6,0.3,1),25))
        l.add_widget(lbl("月よの川の川ソ",26,G,50))
        l.add_widget(lbl("VF Cash Pro",15,D,30))
        l.add_widget(Label(size_hint_y=None,height=20))
        b1=btn("دخول",D,52)
        b1.bind(on_press=self.go)
        l.add_widget(b1)
        b2=btn("تواصل واتساب",(0.1,0.5,0.1,1),45)
        b2.bind(on_press=self.wa)
        l.add_widget(b2)
        l.add_widget(Label())
        self.add_widget(l)
    def wa(self,*a):
        try:
            from android import mActivity
            from jnius import autoclass
            I=autoclass("android.content.Intent")
            U=autoclass("android.net.Uri")
            i=I(I.ACTION_VIEW)
            i.setData(U.parse("https://wa.me/201035593484"))
            mActivity.startActivity(i)
        except:pass
    def go(self,*a):
        d=load()
        if d.get("activated"):
            self.manager.current="admin" if d.get("is_admin") else "login"
        else:
            self.manager.current="activate"

class ActivateScreen(Screen):
    def __init__(self,**kw):
        super().__init__(**kw)
        l=BoxLayout(orientation="vertical",padding=[25,60,25,30],spacing=15)
        l.add_widget(lbl("ادخل كود التفعيل",20,G,40))
        self.ci=inp("XXXXXXXX",h=50)
        l.add_widget(self.ci)
        b=btn("تفعيل",D,52)
        b.bind(on_press=self.activate)
        l.add_widget(b)
        self.st=lbl("",13,R,35)
        l.add_widget(self.st)
        l.add_widget(Label())
        self.add_widget(l)
    def activate(self,*a):
        code=self.ci.text.strip().upper()
        if not code:self.st.text="ادخل الكود";return
        self.st.text="جاري التحقق..."
        threading.Thread(target=self._check,args=(code,),daemon=True).start()
    def _check(self,code):
        try:
            ok,t=check_code(code)
            if ok:
                use_code(code)
                d=load()
                d["activated"]=True
                d["is_admin"]=(t=="admin")
                save(d.get("seamless",""),d.get("token",""),d.get("msisdn",""))
                p=os.path.expanduser("~/.vcash.json")
                dd=json.load(open(p))
                dd["activated"]=True
                dd["is_admin"]=(t=="admin")
                open(p,"w").write(json.dumps(dd))
                nxt="admin" if t=="admin" else "login"
                Clock.schedule_once(lambda dt:setattr(self.manager,"current",nxt),0)
            else:
                Clock.schedule_once(lambda dt:setattr(self.st,"text","كود غلط او مستخدم"),0)
        except Exception as e:
            Clock.schedule_once(lambda dt:setattr(self.st,"text",str(e)),0)

class AdminScreen(Screen):
    def __init__(self,**kw):
        super().__init__(**kw)
        l=BoxLayout(orientation="vertical",padding=[20,30,20,20],spacing=12)
        l.add_widget(lbl("لوحة الادمن",22,G,45))
        l.add_widget(lbl("月よの川の川ソ",14,D,25))
        b1=btn("طلع كود مستخدم جديد",D,52)
        b1.bind(on_press=self.gen)
        l.add_widget(b1)
        self.cl=lbl("",26,G,55)
        l.add_widget(self.cl)
        b2=btn("الشاشة الرئيسية",(0.1,0.3,0.1,1),45)
        b2.bind(on_press=lambda x:setattr(self.manager,"current","login"))
        l.add_widget(b2)
        b3=btn("سجل كل العمليات",(0.1,0.1,0.3,1),45)
        b3.bind(on_press=lambda x:setattr(self.manager,"current","logs"))
        l.add_widget(b3)
        l.add_widget(Label())
        self.add_widget(l)
    def gen(self,*a):
        code=gen_code()
        add_code(code,"user")
        self.cl.text=code

class LoginScreen(Screen):
    def __init__(self,**kw):
        super().__init__(**kw)
        l=BoxLayout(orientation="vertical",padding=[25,50,25,30],spacing=15)
        l.add_widget(lbl("تسجيل الدخول",22,G,45))
        self.st=lbl("اضغط للدخول بالداتا",13,D,30)
        l.add_widget(self.st)
        b1=btn("دخول بالداتا",D,52)
        b1.bind(on_press=self.login)
        l.add_widget(b1)
        b2=btn("عندي توكن محفوظ",(0.1,0.3,0.1,1),45)
        b2.bind(on_press=self.saved)
        l.add_widget(b2)
        l.add_widget(Label())
        self.add_widget(l)
    def login(self,*a):
        self.st.text="جاري الدخول..."
        threading.Thread(target=self._login,daemon=True).start()
    def _login(self):
        try:
            s,m=get_seamless()
            t=get_token(s)
            d=load()
            activated=d.get("activated",False)
            is_admin=d.get("is_admin",False)
            save(s,t,m)
            p=os.path.expanduser("~/.vcash.json")
            dd=json.load(open(p))
            dd["activated"]=activated
            dd["is_admin"]=is_admin
            open(p,"w").write(json.dumps(dd))
            Clock.schedule_once(lambda dt:self._go(m),0)
        except Exception as e:
            Clock.schedule_once(lambda dt:setattr(self.st,"text",str(e)),0)
    def saved(self,*a):
        d=load()
        if d.get("msisdn"):self._go(d["msisdn"])
        else:self.st.text="مفيش توكن، ادخل بالداتا"
    def _go(self,m):
        self.manager.get_screen("home").set_msisdn(m)
        self.manager.current="home"

class HomeScreen(Screen):
    def __init__(self,**kw):
        super().__init__(**kw)
        l=BoxLayout(orientation="vertical",padding=[20,15,20,15],spacing=8)
        self.ml=lbl("",13,D,30)
        l.add_widget(self.ml)
        l.add_widget(lbl("اختار الكارت:",13,(0.7,0.6,0.3,1),25))
        self.sp=Spinner(text=all_products[0],values=all_products,font_size=13,size_hint_y=None,height=42,background_color=(0.1,0.06,0,1),color=G,background_normal="")
        l.add_widget(self.sp)
        l.add_widget(lbl("رقم المستلم:",13,(0.7,0.6,0.3,1),25))
        self.ri=inp("01xxxxxxxxx")
        l.add_widget(self.ri)
        l.add_widget(lbl("الرقم السري:",13,(0.7,0.6,0.3,1),25))
        self.pi=inp("******",pw=True)
        l.add_widget(self.pi)
        l.add_widget(Label(size_hint_y=None,height=8))
        b=btn("ارسال",D,52)
        b.bind(on_press=self.send)
        l.add_widget(b)
        self.st=lbl("",13,G,35)
        l.add_widget(self.st)
        row=BoxLayout(size_hint_y=None,height=42,spacing=10)
        bl=btn("سجل العمليات",(0.1,0.1,0.3,1),42)
        bl.bind(on_press=lambda x:setattr(self.manager,"current","logs"))
        bo=btn("خروج",(0.3,0,0,1),42)
        bo.bind(on_press=self.logout)
        row.add_widget(bl)
        row.add_widget(bo)
        l.add_widget(row)
        self.add_widget(l)
    def set_msisdn(self,m):
        self.ml.text="رقمك: "+str(m)
    def send(self,*a):
        r=self.ri.text.strip()
        p=self.pi.text.strip()
        if not(r.startswith("01") and len(r)==11 and r.isdigit()):
            self.st.text="رقم المستلم غلط";self.st.color=R;return
        if not(p.isdigit() and len(p)==6):
            self.st.text="الرقم السري 6 ارقام";self.st.color=R;return
        self.st.text="جاري الارسال...";self.st.color=G
        threading.Thread(target=self._send,args=(r,p),daemon=True).start()
    def _send(self,r,p):
        try:
            d=load()
            t=get_token(d["seamless"])
            resp=send(t,d["msisdn"],self.sp.text,r,p)
            ok,msg=check_result(resp)
            color=GR if ok else R
            status="success" if ok else "failed"
            log_op(d["msisdn"],self.sp.text,r,status,resp.status_code)
            Clock.schedule_once(lambda dt:(setattr(self.st,"text",msg),setattr(self.st,"color",color)),0)
        except Exception as e:
            Clock.schedule_once(lambda dt:setattr(self.st,"text",str(e)),0)
    def logout(self,*a):
        clear()
        self.manager.current="splash"

class LogsScreen(Screen):
    def __init__(self,**kw):
        super().__init__(**kw)
        self.main=BoxLayout(orientation="vertical",padding=[15,15,15,15],spacing=10)
        self.main.add_widget(lbl("سجل العمليات",20,G,40))
        self.stats=lbl("",13,D,30)
        self.main.add_widget(self.stats)
        sv=ScrollView()
        self.lb=BoxLayout(orientation="vertical",size_hint_y=None,spacing=6)
        self.lb.bind(minimum_height=self.lb.setter("height"))
        sv.add_widget(self.lb)
        self.main.add_widget(sv)
        b=btn("رجوع",(0.2,0.2,0.2,1),45)
        b.bind(on_press=lambda x:setattr(self.manager,"current","home"))
        self.main.add_widget(b)
        self.add_widget(self.main)
    def on_enter(self):
        self.lb.clear_widgets()
        self.stats.text="جاري التحميل..."
        threading.Thread(target=self._load,daemon=True).start()
    def _load(self):
        try:
            logs=get_logs()
            total=len(logs)
            ok=sum(1 for v in logs.values() if v.get("status")=="success")
            Clock.schedule_once(lambda dt:setattr(self.stats,"text",f"الاجمالي: {total}  ناجح: {ok}  فاشل: {total-ok}"),0)
            for k,v in list(logs.items())[-20:]:
                s=v.get("status")=="success"
                t=v.get("time","")[:16]
                txt=f"{'ناجح' if s else 'فاشل'}  {v.get('product','')}  {v.get('receiver','')}  {t}"
                lw=Label(text=txt,font_size=11,size_hint_y=None,height=38,color=GR if s else R,halign="center")
                lw.bind(size=lw.setter("text_size"))
                Clock.schedule_once(lambda dt,w=lw:self.lb.add_widget(w),0)
        except Exception as e:
            Clock.schedule_once(lambda dt:self.lb.add_widget(Label(text=str(e),font_size=12,size_hint_y=None,height=40,color=R)),0)

class VFApp(App):
    def build(self):
        sm=ScreenManager()
        sm.add_widget(SplashScreen(name="splash"))
        sm.add_widget(ActivateScreen(name="activate"))
        sm.add_widget(AdminScreen(name="admin"))
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(LogsScreen(name="logs"))
        return sm

if __name__=="__main__":
    VFApp().run()
