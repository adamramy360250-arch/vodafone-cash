
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
from kivy.graphics import Color, Rectangle, RoundedRectangle
from api import all_products, get_seamless, get_token, send, check_result
from storage import save, load, clear
from firebase import check_code, use_code, add_code, gen_code, log_op, get_logs

Window.clearcolor = (0.05, 0.03, 0, 1)

def ar(text):
    try:
        from bidi.algorithm import get_display
        from arabic_reshaper import reshape
        return get_display(reshape(text))
    except:
        return text

def make_btn(text, color=(0.8,0.53,0,1), height=50):
    return Button(
        text=text, font_size=16,
        size_hint_y=None, height=height,
        background_color=color,
        background_normal="",
        bold=True, color=(1,1,1,1)
    )

def make_lbl(text, size=15, color=(1,0.85,0.2,1), height=35):
    l = Label(
        text=text, font_size=size,
        size_hint_y=None, height=height,
        color=color, halign="center", valign="middle"
    )
    l.bind(size=l.setter("text_size"))
    return l

def make_inp(hint, pw=False, height=45):
    return TextInput(
        hint_text=hint, font_size=15,
        size_hint_y=None, height=height,
        multiline=False, password=pw,
        background_color=(0.1,0.06,0,1),
        foreground_color=(1,0.85,0.2,1),
        hint_text_color=(0.5,0.4,0,1),
        cursor_color=(1,0.85,0.2,1),
        padding=[10,10]
    )

class SplashScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        layout = BoxLayout(orientation="vertical", padding=[25,60,25,30], spacing=15)
        layout.add_widget(make_lbl("Developer", 13, (0.7,0.6,0.3,1), 25))
        layout.add_widget(make_lbl("VF Cash Pro", 30, (1,0.85,0.2,1), 55))
        layout.add_widget(make_lbl("Moon River Cash", 14, (0.8,0.53,0,1), 30))
        layout.add_widget(Label(size_hint_y=None, height=30))
        b1 = make_btn("Login", height=52)
        b1.bind(on_press=self.go)
        layout.add_widget(b1)
        b2 = make_btn("WhatsApp", (0.1,0.5,0.1,1), 45)
        b2.bind(on_press=self.wa)
        layout.add_widget(b2)
        layout.add_widget(Label())
        self.add_widget(layout)

    def wa(self, *a):
        try:
            from android import mActivity
            from jnius import autoclass
            I = autoclass("android.content.Intent")
            U = autoclass("android.net.Uri")
            i = I(I.ACTION_VIEW)
            i.setData(U.parse("https://wa.me/201035593484"))
            mActivity.startActivity(i)
        except:
            pass

    def go(self, *a):
        d = load()
        if d.get("activated"):
            self.manager.current = "admin" if d.get("is_admin") else "login"
        else:
            self.manager.current = "activate"

class ActivateScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        layout = BoxLayout(orientation="vertical", padding=[25,80,25,30], spacing=15)
        layout.add_widget(make_lbl("Enter Activation Code", 18, (1,0.85,0.2,1), 40))
        self.code_inp = make_inp("XXXXXXXX", height=52)
        self.code_inp.font_size = 22
        layout.add_widget(self.code_inp)
        b = make_btn("Activate", height=52)
        b.bind(on_press=self.activate)
        layout.add_widget(b)
        self.status = make_lbl("", 13, (1,0.3,0.3,1), 35)
        layout.add_widget(self.status)
        layout.add_widget(Label())
        self.add_widget(layout)

    def activate(self, *a):
        code = self.code_inp.text.strip().upper()
        if not code:
            self.status.text = "Enter code"
            return
        self.status.text = "Checking..."
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
                Clock.schedule_once(lambda dt: setattr(self.status, "text", "Wrong or used code"), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self.status, "text", str(e)), 0)

class AdminScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        layout = BoxLayout(orientation="vertical", padding=[20,40,20,20], spacing=15)
        layout.add_widget(make_lbl("Admin Panel", 24, (1,0.85,0.2,1), 50))
        layout.add_widget(make_lbl("Moon River Cash", 14, (0.8,0.53,0,1), 28))
        b1 = make_btn("Generate User Code", height=52)
        b1.bind(on_press=self.gen)
        layout.add_widget(b1)
        self.code_lbl = make_lbl("", 28, (1,0.85,0.2,1), 60)
        layout.add_widget(self.code_lbl)
        b2 = make_btn("Main Screen", (0.1,0.3,0.1,1), 48)
        b2.bind(on_press=lambda x: setattr(self.manager, "current", "login"))
        layout.add_widget(b2)
        b3 = make_btn("All Operations Log", (0.1,0.1,0.4,1), 48)
        b3.bind(on_press=lambda x: setattr(self.manager, "current", "logs"))
        layout.add_widget(b3)
        layout.add_widget(Label())
        self.add_widget(layout)

    def gen(self, *a):
        code = gen_code()
        add_code(code, "user")
        self.code_lbl.text = code

class LoginScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        layout = BoxLayout(orientation="vertical", padding=[25,80,25,30], spacing=15)
        layout.add_widget(make_lbl("VF Cash Login", 22, (1,0.85,0.2,1), 45))
        self.status = make_lbl("Press login with Data", 13, (0.8,0.53,0,1), 30)
        layout.add_widget(self.status)
        b1 = make_btn("Login with Data", height=52)
        b1.bind(on_press=self.login)
        layout.add_widget(b1)
        b2 = make_btn("Use Saved Token", (0.1,0.3,0.1,1), 48)
        b2.bind(on_press=self.saved)
        layout.add_widget(b2)
        layout.add_widget(Label())
        self.add_widget(layout)

    def login(self, *a):
        self.status.text = "Logging in..."
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
            Clock.schedule_once(lambda dt: setattr(self.status, "text", str(e)), 0)

    def saved(self, *a):
        d = load()
        if d.get("msisdn"):
            self._go(d["msisdn"])
        else:
            self.status.text = "No saved token"

    def _go(self, m):
        self.manager.get_screen("home").set_msisdn(m)
        self.manager.current = "home"

class HomeScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        layout = BoxLayout(orientation="vertical", padding=[20,15,20,15], spacing=8)
        self.msisdn_lbl = make_lbl("", 13, (0.8,0.53,0,1), 30)
        layout.add_widget(self.msisdn_lbl)
        layout.add_widget(make_lbl("Select Card:", 13, (0.7,0.6,0.3,1), 25))
        self.spinner = Spinner(
            text=all_products[0], values=all_products,
            font_size=13, size_hint_y=None, height=42,
            background_color=(0.1,0.06,0,1), color=(1,0.85,0.2,1),
            background_normal=""
        )
        layout.add_widget(self.spinner)
        layout.add_widget(make_lbl("Receiver Number:", 13, (0.7,0.6,0.3,1), 25))
        self.receiver = make_inp("01xxxxxxxxx")
        layout.add_widget(self.receiver)
        layout.add_widget(make_lbl("PIN (6 digits):", 13, (0.7,0.6,0.3,1), 25))
        self.pin = make_inp("******", pw=True)
        layout.add_widget(self.pin)
        layout.add_widget(Label(size_hint_y=None, height=8))
        btn = make_btn("SEND", height=55)
        btn.bind(on_press=self.do_send)
        layout.add_widget(btn)
        self.status = make_lbl("", 13, (1,0.85,0.2,1), 35)
        layout.add_widget(self.status)
        row = BoxLayout(size_hint_y=None, height=42, spacing=10)
        bl = make_btn("Operations Log", (0.1,0.1,0.3,1), 42)
        bl.bind(on_press=lambda x: setattr(self.manager, "current", "logs"))
        bo = make_btn("Logout", (0.4,0,0,1), 42)
        bo.bind(on_press=self.logout)
        row.add_widget(bl)
        row.add_widget(bo)
        layout.add_widget(row)
        self.add_widget(layout)

    def set_msisdn(self, m):
        self.msisdn_lbl.text = "Your number: " + str(m)

    def do_send(self, *a):
        r = self.receiver.text.strip()
        p = self.pin.text.strip()
        if not (r.startswith("01") and len(r) == 11 and r.isdigit()):
            self.status.text = "Wrong receiver number"
            self.status.color = (1,0.3,0.3,1)
            return
        if not (p.isdigit() and len(p) == 6):
            self.status.text = "PIN must be 6 digits"
            self.status.color = (1,0.3,0.3,1)
            return
        self.status.text = "Sending..."
        self.status.color = (1,0.85,0.2,1)
        threading.Thread(target=self._send, args=(r, p), daemon=True).start()

    def _send(self, r, p):
        try:
            d = load()
            t = get_token(d["seamless"])
            resp = send(t, d["msisdn"], self.spinner.text, r, p)
            ok, msg = check_result(resp)
            color = (0.1,0.7,0.1,1) if ok else (1,0.3,0.3,1)
            status = "success" if ok else "failed"
            log_op(d["msisdn"], self.spinner.text, r, status, resp.status_code)
            Clock.schedule_once(lambda dt: (setattr(self.status, "text", msg), setattr(self.status, "color", color)), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self.status, "text", str(e)), 0)

    def logout(self, *a):
        clear()
        self.manager.current = "splash"

class LogsScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        main = BoxLayout(orientation="vertical", padding=[15,15,15,15], spacing=10)
        main.add_widget(make_lbl("Operations Log", 20, (1,0.85,0.2,1), 40))
        self.stats = make_lbl("", 13, (0.8,0.53,0,1), 30)
        main.add_widget(self.stats)
        sv = ScrollView()
        self.lb = BoxLayout(orientation="vertical", size_hint_y=None, spacing=6)
        self.lb.bind(minimum_height=self.lb.setter("height"))
        sv.add_widget(self.lb)
        main.add_widget(sv)
        b = make_btn("Back", (0.2,0.2,0.2,1), 45)
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
            ok = sum(1 for v in logs.values() if v.get("status") == "success")
            Clock.schedule_once(lambda dt: setattr(self.stats, "text", f"Total: {total}  Success: {ok}  Failed: {total-ok}"), 0)
            for k, v in list(logs.items())[-20:]:
                s = v.get("status") == "success"
                t = v.get("time", "")[:16]
                txt = f"{'OK' if s else 'FAIL'}  {v.get('product','')}  {v.get('receiver','')}  {t}"
                lw = Label(text=txt, font_size=11, size_hint_y=None, height=38,
                          color=(0.1,0.7,0.1,1) if s else (1,0.3,0.3,1), halign="center")
                lw.bind(size=lw.setter("text_size"))
                Clock.schedule_once(lambda dt, w=lw: self.lb.add_widget(w), 0)
        except Exception as e:
            lw = Label(text=str(e), font_size=12, size_hint_y=None, height=40, color=(1,0.3,0.3,1))
            Clock.schedule_once(lambda dt: self.lb.add_widget(lw), 0)

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
