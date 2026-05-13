
import os, json, threading
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line, Ellipse
from api import all_products, get_seamless, get_token, send, check_result
from storage import save, load, clear
from firebase import check_code, use_code, add_code, gen_code, log_op, get_logs

Window.clearcolor = (0.04, 0.02, 0, 1)
GOLD = (1, 0.85, 0.2, 1)
DARK_GOLD = (0.8, 0.53, 0, 1)
RED = (0.9, 0.1, 0.1, 1)
GREEN = (0.1, 0.75, 0.1, 1)
BG2 = (0.08, 0.05, 0, 1)

def gold_card(widget):
    with widget.canvas.before:
        Color(0.15, 0.08, 0, 1)
        widget._rect = RoundedRectangle(pos=widget.pos, size=widget.size, radius=[12])
        Color(0.8, 0.53, 0, 0.4)
        widget._border = RoundedRectangle(pos=(widget.x+1, widget.y+1), size=(widget.width-2, widget.height-2), radius=[12])
    widget.bind(pos=lambda w,v: [setattr(w._rect,"pos",v), setattr(w._border,"pos",(v[0]+1,v[1]+1))])
    widget.bind(size=lambda w,v: [setattr(w._rect,"size",v), setattr(w._border,"size",(v[0]-2,v[1]-2))])

def gbtn(text, color=None, h=50):
    b = Button(text=text, font_size=16, size_hint_y=None, height=h,
               background_color=color or DARK_GOLD, background_normal="",
               bold=True, color=(0.05,0.02,0,1))
    return b

def glbl(text, size=15, color=None, h=35):
    l = Label(text=text, font_size=size, size_hint_y=None, height=h,
              color=color or GOLD, halign="center", valign="middle")
    l.bind(size=l.setter("text_size"))
    return l

def ginp(hint, pw=False, h=45):
    return TextInput(hint_text=hint, font_size=15, size_hint_y=None, height=h,
                     multiline=False, password=pw, background_color=BG2,
                     foreground_color=GOLD, hint_text_color=(0.5,0.4,0,1),
                     cursor_color=GOLD, padding=[12,12])

class SplashScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        with self.canvas.before:
            Color(0.04, 0.02, 0, 1)
            self._bg = Rectangle(pos=self.pos, size=self.size)
            Color(0.8, 0.53, 0, 0.05)
            self._bg2 = Rectangle(pos=self.pos, size=self.size)
        self.bind(size=lambda w,v: [setattr(w._bg,"size",v), setattr(w._bg2,"size",v)])
        self.bind(pos=lambda w,v: [setattr(w._bg,"pos",v), setattr(w._bg2,"pos",v)])

        main = BoxLayout(orientation="vertical", padding=[30,60,30,40], spacing=18)

        # Header box
        header = BoxLayout(orientation="vertical", size_hint_y=None, height=140, padding=[15,10])
        gold_card(header)
        header.add_widget(glbl("月よの川の川ソ", 22, GOLD, 45))
        header.add_widget(glbl("VF Cash Pro", 16, DARK_GOLD, 30))
        header.add_widget(glbl("Developer", 12, (0.6,0.5,0.2,1), 25))
        main.add_widget(header)

        main.add_widget(Label(size_hint_y=None, height=20))

        # Crown decoration
        crown = Label(text="♔", font_size=60, size_hint_y=None, height=80, color=DARK_GOLD)
        main.add_widget(crown)

        # Circle VF
        circle_box = BoxLayout(size_hint_y=None, height=100)
        circle_lbl = Label(text="VF\nCASH", font_size=20, color=GOLD, bold=True, halign="center")
        circle_box.add_widget(circle_lbl)
        main.add_widget(circle_box)

        main.add_widget(Label(size_hint_y=None, height=15))

        b1 = gbtn("Login", DARK_GOLD, 55)
        b1.bind(on_press=self.go)
        main.add_widget(b1)

        b2 = gbtn("WhatsApp", (0.05,0.35,0.05,1), 48)
        b2.bind(on_press=self.wa)
        main.add_widget(b2)

        main.add_widget(Label())
        self.add_widget(main)

    def wa(self, *a):
        try:
            from android import mActivity
            from jnius import autoclass
            I = autoclass("android.content.Intent")
            U = autoclass("android.net.Uri")
            i = I(I.ACTION_VIEW)
            i.setData(U.parse("https://wa.me/201035593484"))
            mActivity.startActivity(i)
        except: pass

    def go(self, *a):
        d = load()
        if d.get("activated"):
            self.manager.current = "admin" if d.get("is_admin") else "login"
        else:
            self.manager.current = "activate"

class ActivateScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation="vertical", padding=[25,100,25,30], spacing=18)
        l.add_widget(glbl("Enter Activation Code", 20, GOLD, 45))
        l.add_widget(Label(size_hint_y=None, height=10))
        self.ci = ginp("XXXXXXXX", h=55)
        self.ci.font_size = 24
        l.add_widget(self.ci)
        l.add_widget(Label(size_hint_y=None, height=10))
        b = gbtn("Activate", h=55)
        b.bind(on_press=self.activate)
        l.add_widget(b)
        self.st = glbl("", 14, RED, 40)
        l.add_widget(self.st)
        l.add_widget(Label())
        self.add_widget(l)

    def activate(self, *a):
        code = self.ci.text.strip().upper()
        if not code: self.st.text = "Enter code"; return
        self.st.text = "Checking..."
        self.st.color = GOLD
        threading.Thread(target=self._check, args=(code,), daemon=True).start()

    def _check(self, code):
        try:
            ok, t = check_code(code)
            if ok:
                use_code(code)
                path = os.path.expanduser("~/.vcash.json")
                d = {}
                if os.path.exists(path):
                    try: d = json.load(open(path))
                    except: d = {}
                d["activated"] = True
                d["is_admin"] = (t == "admin")
                d.setdefault("seamless", "")
                d.setdefault("token", "")
                d.setdefault("msisdn", "")
                open(path, "w").write(json.dumps(d))
                nxt = "admin" if t == "admin" else "login"
                Clock.schedule_once(lambda dt: setattr(self.manager, "current", nxt), 0)
            else:
                Clock.schedule_once(lambda dt: [setattr(self.st,"text","Wrong or used code"), setattr(self.st,"color",RED)], 0)
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self.st, "text", str(e)), 0)

class AdminScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation="vertical", padding=[20,50,20,20], spacing=18)
        l.add_widget(glbl("Admin Panel", 26, GOLD, 55))
        l.add_widget(glbl("Moon River Cash", 14, DARK_GOLD, 28))
        l.add_widget(Label(size_hint_y=None, height=10))
        b1 = gbtn("Generate User Code", h=55)
        b1.bind(on_press=self.gen)
        l.add_widget(b1)
        self.cl = glbl("", 30, GOLD, 65)
        l.add_widget(self.cl)
        l.add_widget(Label(size_hint_y=None, height=10))
        b2 = gbtn("Main Screen", (0.05,0.3,0.05,1), 50)
        b2.bind(on_press=lambda x: setattr(self.manager, "current", "login"))
        l.add_widget(b2)
        b3 = gbtn("All Logs", (0.05,0.05,0.35,1), 50)
        b3.bind(on_press=lambda x: setattr(self.manager, "current", "logs"))
        l.add_widget(b3)
        l.add_widget(Label())
        self.add_widget(l)

    def gen(self, *a):
        code = gen_code()
        add_code(code, "user")
        self.cl.text = code

class LoginScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation="vertical", padding=[25,100,25,30], spacing=18)
        l.add_widget(glbl("VF Cash Login", 24, GOLD, 50))
        self.st = glbl("Press login with Data", 14, DARK_GOLD, 32)
        l.add_widget(self.st)
        l.add_widget(Label(size_hint_y=None, height=15))
        b1 = gbtn("Login with Data", h=55)
        b1.bind(on_press=self.login)
        l.add_widget(b1)
        b2 = gbtn("Use Saved Token", (0.05,0.3,0.05,1), 50)
        b2.bind(on_press=self.saved)
        l.add_widget(b2)
        l.add_widget(Label())
        self.add_widget(l)

    def login(self, *a):
        self.st.text = "Logging in..."
        threading.Thread(target=self._login, daemon=True).start()

    def _login(self):
        try:
            s, m = get_seamless()
            t = get_token(s)
            d = load()
            activated = d.get("activated", False)
            is_admin = d.get("is_admin", False)
            save(s, t, m)
            path = os.path.expanduser("~/.vcash.json")
            dd = json.load(open(path))
            dd["activated"] = activated
            dd["is_admin"] = is_admin
            open(path, "w").write(json.dumps(dd))
            Clock.schedule_once(lambda dt: self._go(m), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self.st, "text", str(e)), 0)

    def saved(self, *a):
        d = load()
        if d.get("msisdn"): self._go(d["msisdn"])
        else: self.st.text = "No saved token"

    def _go(self, m):
        self.manager.get_screen("home").set_msisdn(m)
        self.manager.current = "home"

class HomeScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation="vertical", padding=[20,15,20,15], spacing=8)

        # number badge
        num_box = BoxLayout(size_hint_y=None, height=40, padding=[10,5])
        gold_card(num_box)
        self.ml = glbl("", 13, DARK_GOLD, 30)
        num_box.add_widget(self.ml)
        l.add_widget(num_box)

        l.add_widget(glbl("Select Card:", 13, (0.7,0.6,0.3,1), 25))
        self.sp = Spinner(text=all_products[0], values=all_products, font_size=13,
                          size_hint_y=None, height=45, background_color=BG2,
                          color=GOLD, background_normal="")
        l.add_widget(self.sp)

        l.add_widget(glbl("Receiver Number:", 13, (0.7,0.6,0.3,1), 25))
        self.ri = ginp("01xxxxxxxxx")
        l.add_widget(self.ri)

        l.add_widget(glbl("PIN (6 digits):", 13, (0.7,0.6,0.3,1), 25))
        self.pi = ginp("******", pw=True)
        l.add_widget(self.pi)

        l.add_widget(Label(size_hint_y=None, height=8))
        b = gbtn("SEND", DARK_GOLD, 55)
        b.bind(on_press=self.do_send)
        l.add_widget(b)

        self.st = glbl("", 13, GOLD, 35)
        l.add_widget(self.st)

        row = BoxLayout(size_hint_y=None, height=45, spacing=10)
        bl = gbtn("Logs", (0.05,0.05,0.35,1), 45)
        bl.bind(on_press=lambda x: setattr(self.manager, "current", "logs"))
        bo = gbtn("Logout", (0.4,0,0,1), 45)
        bo.bind(on_press=self.logout)
        row.add_widget(bl)
        row.add_widget(bo)
        l.add_widget(row)
        self.add_widget(l)

    def set_msisdn(self, m):
        self.ml.text = "Number: " + str(m)

    def do_send(self, *a):
        r = self.ri.text.strip()
        p = self.pi.text.strip()
        if not (r.startswith("01") and len(r)==11 and r.isdigit()):
            self.st.text = "Wrong number"; self.st.color = RED; return
        if not (p.isdigit() and len(p)==6):
            self.st.text = "PIN 6 digits"; self.st.color = RED; return
        self.st.text = "Sending..."; self.st.color = GOLD
        threading.Thread(target=self._send, args=(r,p), daemon=True).start()

    def _send(self, r, p):
        try:
            d = load()
            t = get_token(d["seamless"])
            resp = send(t, d["msisdn"], self.sp.text, r, p)
            ok, msg = check_result(resp)
            color = GREEN if ok else RED
            log_op(d["msisdn"], self.sp.text, r, "success" if ok else "failed", resp.status_code)
            Clock.schedule_once(lambda dt: [setattr(self.st,"text",msg), setattr(self.st,"color",color)], 0)
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self.st, "text", str(e)), 0)

    def logout(self, *a):
        clear(); self.manager.current = "splash"

class LogsScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        main = BoxLayout(orientation="vertical", padding=[15,15,15,15], spacing=10)
        main.add_widget(glbl("Operations Log", 22, GOLD, 45))
        self.stats = glbl("", 13, DARK_GOLD, 32)
        main.add_widget(self.stats)
        sv = ScrollView()
        self.lb = BoxLayout(orientation="vertical", size_hint_y=None, spacing=6)
        self.lb.bind(minimum_height=self.lb.setter("height"))
        sv.add_widget(self.lb)
        main.add_widget(sv)
        b = gbtn("Back", (0.2,0.2,0.2,1), 45)
        b.bind(on_press=lambda x: setattr(self.manager, "current", "home"))
        main.add_widget(b)
        self.add_widget(main)

    def on_enter(self):
        self.lb.clear_widgets()
        self.stats.text = "Loading..."
        threading.Thread(target=self._load, daemon=True).start()

    def _load(self):
        try:
            logs = get_logs()
            total = len(logs)
            ok = sum(1 for v in logs.values() if v.get("status")=="success")
            Clock.schedule_once(lambda dt: setattr(self.stats,"text",f"Total:{total} OK:{ok} Fail:{total-ok}"), 0)
            for k, v in list(logs.items())[-20:]:
                s = v.get("status") == "success"
                txt = f"{'OK' if s else 'FAIL'}  {v.get('product','')}  {v.get('receiver','')}  {v.get('time','')[:16]}"
                lw = Label(text=txt, font_size=11, size_hint_y=None, height=40,
                           color=GREEN if s else RED, halign="center")
                lw.bind(size=lw.setter("text_size"))
                Clock.schedule_once(lambda dt, w=lw: self.lb.add_widget(w), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt: self.lb.add_widget(
                Label(text=str(e), font_size=12, size_hint_y=None, height=40, color=RED)), 0)

class VFApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(SplashScreen(name="splash"))
        sm.add_widget(ActivateScreen(name="activate"))
        sm.add_widget(AdminScreen(name="admin"))
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(LogsScreen(name="logs"))
        return sm

if __name__ == "__main__":
    VFApp().run()
