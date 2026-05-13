
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
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from api import all_products, get_seamless, get_token, send, check_result
from storage import save, load, clear
from firebase import check_code, use_code, add_code, gen_code, log_op, get_logs

Window.clearcolor = (0.04, 0.02, 0, 1)

GOLD = (1, 0.85, 0.2, 1)
DARK_GOLD = (0.8, 0.53, 0, 1)
RED = (0.8, 0.1, 0.1, 1)
GREEN = (0.1, 0.7, 0.1, 1)
BG = (0.04, 0.02, 0, 1)
BG2 = (0.1, 0.06, 0, 1)

def gold_btn(text, color=None, h=50):
    return Button(text=text, font_size=16, size_hint_y=None, height=h,
                  background_color=color or DARK_GOLD, background_normal="",
                  bold=True, color=(0.05,0.02,0,1))

def lbl(text, size=15, color=None, h=35):
    l = Label(text=text, font_size=size, size_hint_y=None, height=h,
              color=color or GOLD, halign="center", valign="middle")
    l.bind(size=l.setter("text_size"))
    return l

def inp(hint, pw=False, h=45):
    return TextInput(hint_text=hint, font_size=15, size_hint_y=None, height=h,
                     multiline=False, password=pw, background_color=BG2,
                     foreground_color=GOLD, hint_text_color=(0.5,0.4,0,1),
                     cursor_color=GOLD, padding=[10,10])

def add_gold_bg(widget):
    with widget.canvas.before:
        Color(0.04, 0.02, 0, 1)
        widget._bg = Rectangle(pos=widget.pos, size=widget.size)
        Color(0.8, 0.53, 0, 0.15)
        widget._border = RoundedRectangle(pos=widget.pos, size=widget.size, radius=[10])
    widget.bind(pos=lambda w,v: setattr(w._bg, "pos", v))
    widget.bind(size=lambda w,v: setattr(w._bg, "size", v))

class SplashScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        with self.canvas.before:
            Color(0.04, 0.02, 0, 1)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(size=lambda w,v: setattr(w._bg, "size", v))
        self.bind(pos=lambda w,v: setattr(w._bg, "pos", v))
        l = BoxLayout(orientation="vertical", padding=[30,50,30,30], spacing=15)
        l.add_widget(Label(size_hint_y=None, height=20))
        l.add_widget(lbl("المطور", 13, (0.7,0.6,0.3,1), 25))
        l.add_widget(lbl("VF Cash Pro", 32, GOLD, 55))
        l.add_widget(lbl("Moon River Cash", 16, DARK_GOLD, 30))
        l.add_widget(Label(size_hint_y=None, height=5))
        with l.canvas.before:
            Color(0.8, 0.53, 0, 0.3)
            Line(points=[50, 0, 300, 0], width=1)
        l.add_widget(Label(size_hint_y=None, height=30))
        b1 = gold_btn("Login", DARK_GOLD, 52)
        b1.bind(on_press=self.go)
        l.add_widget(b1)
        b2 = gold_btn("WhatsApp", (0.1,0.5,0.1,1), 45)
        b2.bind(on_press=self.wa)
        l.add_widget(b2)
        l.add_widget(Label())
        self.add_widget(l)

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
        l = BoxLayout(orientation="vertical", padding=[25,80,25,30], spacing=15)
        l.add_widget(lbl("Enter Activation Code", 18, GOLD, 40))
        self.ci = inp("XXXXXXXX", h=52)
        self.ci.font_size = 22
        l.add_widget(self.ci)
        b = gold_btn("Activate", h=52)
        b.bind(on_press=self.activate)
        l.add_widget(b)
        self.st = lbl("", 13, RED, 35)
        l.add_widget(self.st)
        l.add_widget(Label())
        self.add_widget(l)

    def activate(self, *a):
        code = self.ci.text.strip().upper()
        if not code: self.st.text = "Enter code"; return
        self.st.text = "Checking..."
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
                if "seamless" not in d: d["seamless"] = ""
                if "token" not in d: d["token"] = ""
                if "msisdn" not in d: d["msisdn"] = ""
                open(path, "w").write(json.dumps(d))
                nxt = "admin" if t == "admin" else "login"
                Clock.schedule_once(lambda dt: setattr(self.manager, "current", nxt), 0)
            else:
                Clock.schedule_once(lambda dt: setattr(self.st, "text", "Wrong or used code"), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self.st, "text", str(e)), 0)

class AdminScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation="vertical", padding=[20,40,20,20], spacing=15)
        l.add_widget(lbl("Admin Panel", 24, GOLD, 50))
        l.add_widget(lbl("Moon River Cash", 14, DARK_GOLD, 28))
        b1 = gold_btn("Generate User Code", h=52)
        b1.bind(on_press=self.gen)
        l.add_widget(b1)
        self.cl = lbl("", 28, GOLD, 60)
        l.add_widget(self.cl)
        b2 = gold_btn("Main Screen", (0.1,0.3,0.1,1), 48)
        b2.bind(on_press=lambda x: setattr(self.manager, "current", "login"))
        l.add_widget(b2)
        b3 = gold_btn("All Logs", (0.1,0.1,0.4,1), 48)
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
        l = BoxLayout(orientation="vertical", padding=[25,80,25,30], spacing=15)
        l.add_widget(lbl("VF Cash Login", 22, GOLD, 45))
        self.st = lbl("Press login with Data", 13, DARK_GOLD, 30)
        l.add_widget(self.st)
        b1 = gold_btn("Login with Data", h=52)
        b1.bind(on_press=self.login)
        l.add_widget(b1)
        b2 = gold_btn("Use Saved Token", (0.1,0.3,0.1,1), 48)
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
        self.ml = lbl("", 13, DARK_GOLD, 30)
        l.add_widget(self.ml)
        l.add_widget(lbl("Select Card:", 13, (0.7,0.6,0.3,1), 25))
        self.sp = Spinner(text=all_products[0], values=all_products, font_size=13,
                          size_hint_y=None, height=42, background_color=BG2,
                          color=GOLD, background_normal="")
        l.add_widget(self.sp)
        l.add_widget(lbl("Receiver:", 13, (0.7,0.6,0.3,1), 25))
        self.ri = inp("01xxxxxxxxx")
        l.add_widget(self.ri)
        l.add_widget(lbl("PIN (6 digits):", 13, (0.7,0.6,0.3,1), 25))
        self.pi = inp("******", pw=True)
        l.add_widget(self.pi)
        l.add_widget(Label(size_hint_y=None, height=8))
        b = gold_btn("SEND", h=55)
        b.bind(on_press=self.do_send)
        l.add_widget(b)
        self.st = lbl("", 13, GOLD, 35)
        l.add_widget(self.st)
        row = BoxLayout(size_hint_y=None, height=42, spacing=10)
        bl = gold_btn("Logs", (0.1,0.1,0.3,1), 42)
        bl.bind(on_press=lambda x: setattr(self.manager, "current", "logs"))
        bo = gold_btn("Logout", (0.4,0,0,1), 42)
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
            Clock.schedule_once(lambda dt: (setattr(self.st,"text",msg), setattr(self.st,"color",color)), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self.st, "text", str(e)), 0)

    def logout(self, *a):
        clear(); self.manager.current = "splash"

class LogsScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        main = BoxLayout(orientation="vertical", padding=[15,15,15,15], spacing=10)
        main.add_widget(lbl("Operations Log", 20, GOLD, 40))
        self.stats = lbl("", 13, DARK_GOLD, 30)
        main.add_widget(self.stats)
        sv = ScrollView()
        self.lb = BoxLayout(orientation="vertical", size_hint_y=None, spacing=6)
        self.lb.bind(minimum_height=self.lb.setter("height"))
        sv.add_widget(self.lb)
        main.add_widget(sv)
        b = gold_btn("Back", (0.2,0.2,0.2,1), 45)
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
            Clock.schedule_once(lambda dt: setattr(self.stats, "text", f"Total:{total} OK:{ok} Fail:{total-ok}"), 0)
            for k, v in list(logs.items())[-20:]:
                s = v.get("status") == "success"
                txt = f"{'OK' if s else 'FAIL'}  {v.get('product','')}  {v.get('receiver','')}  {v.get('time','')[:16]}"
                lw = Label(text=txt, font_size=11, size_hint_y=None, height=38,
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
