# -*- coding: utf-8 -*-
"""
 SaqrSoft — عميل متابعة حالة الجهاز
 الملف: main.py
"""

import os
import socket
import threading
from datetime import datetime

import requests
from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.switch import Switch
from kivy.uix.textinput import TextInput

# ── (1) الإعدادات ──────────────────────────────────────────
DEFAULT_SERVER_URL = 'https://YOUR-APP.onrender.com/report'
DEFAULT_CHAT_ID = ''        # Chat ID بعد الربط
AUTO_SYNC_MINUTES = 15      # فترة المزامنة التلقائية (دقائق)
HTTP_TIMEOUT = 15           # مهلة الاتصال بالسيرفر (ثوانٍ)

# ألوان الواجهة
COLOR_BG   = (0.05, 0.07, 0.13, 1)
COLOR_CARD = (0.12, 0.16, 0.26, 1)
COLOR_MAIN = (0.20, 0.70, 0.85, 1)
COLOR_TEXT = (0.92, 0.95, 1.00, 1)
COLOR_DIM  = (0.70, 0.75, 0.85, 1)
COLOR_OK   = (0.30, 0.85, 0.45, 1)
COLOR_ERR  = (0.95, 0.40, 0.40, 1)

# ── (2) دعم اللغة العربية ──────────────────────────────────
try:
    import arabic_reshaper
    from bidi.algorithm import get_display

    def ar(text):
        return get_display(arabic_reshaper.reshape(str(text)))
except ImportError:
    def ar(text):
        return str(text)

FONT_NAME = 'Roboto'
for _f in ('data/NotoNaskhArabic-Regular.ttf', 'data/font.ttf'):
    if os.path.exists(_f):
        LabelBase.register(name='ArabicFont', fn_regular=_f)
        FONT_NAME = 'ArabicFont'
        break

# ── (3) جمع بيانات الجهاز ──────────────────────────────────
def get_android_info():
    try:
        from jnius import autoclass

        Build = autoclass('android.os.Build')
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Intent = autoclass('android.content.Intent')
        IntentFilter = autoclass('android.content.IntentFilter')

        ctx = PythonActivity.mActivity
        intent = ctx.registerReceiver(
            None, IntentFilter(Intent.ACTION_BATTERY_CHANGED)
        )
        level = intent.getIntExtra('level', -1)
        scale = intent.getIntExtra('scale', -1)
        battery = int(level * 100 / scale) if scale > 0 else -1

        return {
            'name': str(Build.MODEL),
            'sdk': str(Build.VERSION.SDK_INT),
            'battery': battery,
        }
    except Exception:
        return {'name': 'Test-Device', 'sdk': '0', 'battery': -1}


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return 'غير معروف'


def collect_device_info():
    info = get_android_info()
    info['ip'] = get_local_ip()
    info['time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return info


def info_preview_text(info):
    battery = f"{info['battery']}%" if info['battery'] >= 0 else 'غير متوفرة'
    return (
        f"اسم الجهاز: {info['name']}\n"
        f"إصدار SDK: {info['sdk']}\n"
        f"البطارية: {battery}\n"
        f"عنوان IP: {info['ip']}\n"
        f"الوقت: {info['time']}"
    )

# ── (4) الإرسال إلى السيرفر ────────────────────────────────
def send_report(server_url, chat_id, info):
    battery = info['battery'] if info['battery'] >= 0 else '؟'
    payload = {
        'chat': int(chat_id),
        'name': info['name'],
        'sdk': info['sdk'],
        'text': f"🔋 البطارية {battery}% | 🌐 IP: {info['ip']} | 🕒 {info['time']}",
    }
    r = requests.post(server_url, json=payload, timeout=HTTP_TIMEOUT)
    return r.json()

# ── (5) الواجهة ────────────────────────────────────────────
def make_label(text='', **kw):
    lbl = Label(text=ar(text), font_name=FONT_NAME, **kw)
    lbl.bind(width=lambda inst, w: setattr(inst, 'text_size', (w, None)))
    return lbl


def make_button(text, color, height=55, **kw):
    return Button(
        text=ar(text), font_name=FONT_NAME, size_hint_y=None,
        height=height, background_normal='', background_color=color, **kw
    )


class StatusApp(App):
    title = 'SaqrSoft Status'

    def build(self):
        Window.clearcolor = COLOR_BG
        self.auto_event = None

        root = BoxLayout(orientation='vertical', padding=20, spacing=10)

        root.add_widget(make_label(
            '🦅 SaqrSoft — متابعة حالة الجهاز', font_size=22,
            color=COLOR_MAIN, size_hint_y=None, height=40, bold=True))

        root.add_widget(make_label(
            'قبل الإرسال: أرسل /pair من حساب تليجرامك ثم وافق عليها من المشرف، '
            'واعرف معرّفك من /myid', font_size=13, color=COLOR_DIM,
            size_hint_y=None, height=55))

        root.add_widget(make_label('رابط السيرفر:', font_size=14,
                                   size_hint_y=None, height=25, color=COLOR_TEXT))
        self.url_input = TextInput(
            text=DEFAULT_SERVER_URL, multiline=False, font_name=FONT_NAME,
            size_hint_y=None, height=45, background_color=COLOR_CARD,
            foreground_color=COLOR_TEXT)
        root.add_widget(self.url_input)

        root.add_widget(make_label('معرّف المحادثة Chat ID:', font_size=14,
                                   size_hint_y=None, height=25, color=COLOR_TEXT))
        self.chat_input = TextInput(
            text=DEFAULT_CHAT_ID, multiline=False, font_name=FONT_NAME,
            size_hint_y=None, height=45, input_filter='int',
            background_color=COLOR_CARD, foreground_color=COLOR_TEXT,
            hint_text=ar('ضع الـ Chat ID هنا'))
        root.add_widget(self.chat_input)

        root.add_widget(make_label('ما سيُرسل إلى السيرفر:', font_size=14,
                                   size_hint_y=None, height=25, color=COLOR_MAIN))
        self.preview = make_label('اضغط زر التحديث لعرض البيانات',
                                  font_size=15, color=COLOR_TEXT)
        root.add_widget(self.preview)

        root.add_widget(make_button(
            '🔄 تحديث المعاينة', COLOR_CARD, height=50,
            on_press=self.refresh_preview))

        root.add_widget(make_button(
            '✅ أوافق على إرسال تقرير الحالة الآن', (0.16, 0.55, 0.30, 1),
            height=70, bold=True, on_press=self.on_consent))

        auto_row = BoxLayout(orientation='horizontal',
                             size_hint_y=None, height=45, spacing=10)
        auto_row.add_widget(make_label(
            f'مزامنة تلقائية كل {AUTO_SYNC_MINUTES} دقيقة (أثناء فتح التطبيق فقط)',
            font_size=13, color=COLOR_DIM))
        self.auto_switch = Switch(size_hint_x=None, width=60)
        self.auto_switch.bind(active=self.on_auto_toggle)
        auto_row.add_widget(self.auto_switch)
        root.add_widget(auto_row)

        self.status = make_label('', font_size=14, color=COLOR_MAIN,
                                 size_hint_y=None, height=45)
        root.add_widget(self.status)

        Clock.schedule_once(self.refresh_preview, 0)
        return root

    def refresh_preview(self, *_):
        info = collect_device_info()
        self.preview.text = ar(info_preview_text(info))

    def on_consent(self, *_):
        self._send()

    def on_auto_toggle(self, switch, value):
        if value:
            self._send()
            self.auto_event = Clock.schedule_interval(
                self._auto_tick, AUTO_SYNC_MINUTES * 60)
            self._set_status(
                ar(f'⏱️ المزامنة التلقائية مفعّلة كل {AUTO_SYNC_MINUTES} دقيقة '
                   '(أثناء فتح التطبيق فقط)'), COLOR_MAIN)
        else:
            if self.auto_event:
                self.auto_event.cancel()
                self.auto_event = None
            self._set_status(ar('المزامنة التلقائية موقوفة'), COLOR_DIM)

    def _auto_tick(self, dt):
        self._send()

    def _send(self):
        url = self.url_input.text.strip()
        chat = self.chat_input.text.strip()
        if not chat:
            self._set_status(
                ar('أدخل Chat ID أولاً — اعرفه من أمر /myid في البوت'), COLOR_ERR)
            return
        threading.Thread(
            target=self._send_worker, args=(url, chat), daemon=True).start()

    def _send_worker(self, url, chat):
        try:
            info = collect_device_info()
            data = send_report(url, chat, info)
            if isinstance(data, dict) and data.get('error'):
                self._finish(ar('⚠️ ' + str(data['error'])), COLOR_ERR)
            else:
                self._finish(ar('✅ تم إرسال تقرير الحالة بنجاح'), COLOR_OK)
                self.refresh_preview()
        except ValueError:
            self._finish(
                ar('❌ Chat ID غير صالح — انسخه كما هو من أمر /myid'), COLOR_ERR)
        except requests.exceptions.Timeout:
            self._finish(ar('❌ انتهت مهلة الاتصال بالسيرفر'), COLOR_ERR)
        except requests.exceptions.RequestException:
            self._finish(
                ar('❌ فشل الاتصال — تأكد من رابط السيرفر ومن إنترنت الجهاز'),
                COLOR_ERR)

    @mainthread
    def _finish(self, text, color):
        self._set_status(text, color)

    def _set_status(self, text, color):
        self.status.text = text
        self.status.color = color

    def on_stop(self):
        if self.auto_event:
            self.auto_event.cancel()

if __name__ == '__main__':
    StatusApp().run()
