"""
فراشة النيون — Butterfly Curve with Neon Trails
================================================

رسم متحرك لمنحنى الفراشة (Butterfly Curve) بألوان قوس قزح وتوهج نيون.

    r(t) = e^cos(t) - 2·cos(4t)
    x = r·sin(t) ,  y = r·cos(t)

المنحنى يُرسم 6 مرات (1400 خطوة) وحجمه يصغر ثم يكبر، فتتكوّن طبقات
فراشات متداخلة، ولون كل خطوة يتدرّج من البرتقالي حتى الوردي.

التشغيل:
    python butterfly.py          -> الرسم المتحرك (ويحفظ صورة HD عند الانتهاء)
    python butterfly.py --hd     -> يحفظ صورة HD فقط بدون نافذة

داخل النافذة:
    Space  إعادة الرسم من البداية
    S      حفظ صورة HD الآن
    Esc    خروج
"""

import colorsys
import math
import os
import random
import sys
import tkinter as tk

# ---------------------------------------------------------------- settings
N = 1400              # عدد الخطوات الكلي
LOOPS = 6             # كم مرة يُرسم المنحنى
SUB = 4               # نقاط فرعية لكل خطوة (نعومة الخط)
STEPS_PER_FRAME = 2   # خطوات لكل إطار
FRAME_MS = 16         # زمن الإطار (ms) ~ 60fps
RAY_EVERY = 3         # شعاع من المركز كل كم خطوة
DOT_EVERY = 7         # نقطة مضيئة كل كم خطوة
HD_HEIGHT = 2160      # ارتفاع الصورة المحفوظة
HD_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "butterfly_hd.png")

TITLE = "Butterfly Curve"
SUBTITLE = "with Neon Trails"
BG = (5, 6, 10)


# ---------------------------------------------------------------- math
def curve(k):
    """نقطة المنحنى عند الخطوة k (يمكن أن تكون كسرية) بوحدات المنحنى."""
    t = k / N * LOOPS * 2 * math.pi
    r = math.exp(math.cos(t)) - 2 * math.cos(4 * t)
    # الحجم: 1 في البداية، يصغر في المنتصف، ثم يعود 1 في النهاية
    s = 0.62 + 0.38 * (0.5 + 0.5 * math.cos(2 * math.pi * k / N))
    return r * math.sin(t) * s, r * math.cos(t) * s


def hue(k):
    return (0.02 + 0.90 * k / N) % 1.0          # برتقالي -> أصفر -> أخضر -> أزرق -> وردي


def rgb(k, v=1.0, white=0.0):
    r, g, b = colorsys.hsv_to_rgb(hue(k), 0.9, 1.0)
    r, g, b = (c + (1 - c) * white for c in (r, g, b))
    return r * v, g * v, b * v


def hexc(c):
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(x * 255))) for x in c)


def rgb255(c):
    return tuple(max(0, min(255, round(x * 255))) for x in c)


class Geometry:
    """تحويل وحدات المنحنى إلى بكسلات لأي حجم لوحة."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.sc = h / 900.0                 # معامل الحجم (التصميم مبني على 900px)
        self.u = 0.155 * h
        self.cx, self.cy = w / 2, 0.60 * h

    def px(self, xy):
        x, y = xy
        return self.cx + x * self.u, self.cy - y * self.u

    def seg(self, i, sub):
        return [self.px(curve(i + j / sub)) for j in range(sub + 1)]


# ---------------------------------------------------------------- HD render (Pillow)
def render_hd(path=HD_FILE, height=HD_HEIGHT, upto=N):
    from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

    SS = 2                                   # supersampling لحواف ناعمة
    Wf, Hf = int(height * 1.05), height
    g = Geometry(Wf * SS, Hf * SS)
    w, h, sc = g.w, g.h, g.sc

    def boost(img, k):
        return img.point(lambda v: min(255, int(v * k)))

    # الخلفية + النجوم
    base = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(base)
    rnd = random.Random(7)
    for _ in range(260):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        r = rnd.uniform(0.6, 1.8) * sc
        v = rnd.randint(50, 170)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(v, v, min(255, v + 20)))

    # الأشعة الرفيعة من المركز
    rays = Image.new("RGB", (w, h), (0, 0, 0))
    dr = ImageDraw.Draw(rays)
    # المنحنى نفسه (سيُطمس لاحقاً لصنع التوهج)
    line = Image.new("RGB", (w, h), (0, 0, 0))
    dl = ImageDraw.Draw(line)
    center = (g.cx, g.cy)
    dots = []
    for i in range(upto):
        pts = g.seg(i, 8)
        k = i + 0.5
        if i % RAY_EVERY == 0:
            dr.line([center, pts[-1]], fill=rgb255(rgb(k, 0.42)), width=max(1, round(0.6 * sc)))
        dl.line(pts, fill=rgb255(rgb(k, 1.0, 0.18)), width=round(2.0 * sc), joint="curve")
        if i % DOT_EVERY == 0:
            dots.append((pts[0], k))
    for (x, y), k in dots:
        r = 3.2 * sc
        dl.ellipse((x - r, y - r, x + r, y + r), fill=rgb255(rgb(k, 1.0, 0.35)))

    glow_s = boost(line.filter(ImageFilter.GaussianBlur(4 * sc)), 1.5)
    glow_l = boost(line.filter(ImageFilter.GaussianBlur(16 * sc)), 1.15)

    img = ImageChops.add(base, rays)
    img = ImageChops.add(img, glow_l)
    img = ImageChops.add(img, glow_s)
    img = ImageChops.add(img, line)

    # مراكز بيضاء للنقاط
    d = ImageDraw.Draw(img)
    for (x, y), k in dots:
        r = 1.3 * sc
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255))

    # النصوص
    def font(names, size):
        for n in names:
            try:
                return ImageFont.truetype(n, size)
            except OSError:
                pass
        return ImageFont.load_default(size)

    f_title = font(["segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"], round(40 * sc))
    f_sub = font(["segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"], round(19 * sc))
    f_mono = font(["consola.ttf", "cour.ttf", "DejaVuSansMono.ttf"], round(17 * sc))
    d.text((w / 2, 0.055 * h), TITLE, font=f_title, fill=(255, 255, 255), anchor="mm")
    d.text((w / 2, 0.098 * h), SUBTITLE, font=f_sub, fill=(165, 172, 190), anchor="mm")
    d.line([(w / 2 - 130 * sc, 0.125 * h), (w / 2 + 130 * sc, 0.125 * h)],
           fill=(60, 66, 82), width=max(1, round(1.2 * sc)))
    d.text((w - 26 * sc, h - 22 * sc), f"i = {upto}/{N}", font=f_mono,
           fill=(140, 146, 162), anchor="rs")

    img = img.resize((Wf, Hf), Image.LANCZOS)
    img.save(path)
    return path


# ---------------------------------------------------------------- live animation (tkinter)
LAYERS = ["stars", "rays", "glow", "mid", "core", "dots", "head", "ui"]


class App:
    def __init__(self, root):
        self.root = root
        sh = root.winfo_screenheight()
        H = int(sh * 0.82)
        W = int(H * 1.05)
        self.g = Geometry(W, H)
        sc = self.g.sc
        self.sc = sc

        root.title("فراشة — Butterfly Curve with Neon Trails")
        root.configure(bg=hexc([c / 255 for c in BG]))
        root.resizable(False, False)
        self.cv = cv = tk.Canvas(root, width=W, height=H, bg=hexc([c / 255 for c in BG]),
                                 highlightthickness=0)
        cv.pack()

        # علامات مخفية تحدد ترتيب الطبقات (الأحدث يبقى فوق طبقته فقط)
        self.marker = {}
        for name in LAYERS:
            self.marker[name] = cv.create_line(0, 0, 0, 0, state="hidden")

        # النجوم
        self.stars = []
        rnd = random.Random(7)
        for _ in range(220):
            x, y = rnd.uniform(0, W), rnd.uniform(0, H)
            r = rnd.uniform(0.5, 1.6) * sc
            v = rnd.uniform(0.2, 0.65)
            sid = self.add("stars", cv.create_oval(x - r, y - r, x + r, y + r, width=0,
                                                   fill=hexc((v, v, min(1, v + 0.08)))))
            self.stars.append((sid, v))

        # العنوان
        self.add("ui", cv.create_text(W / 2, 0.055 * H, text=TITLE, fill="#ffffff",
                                      font=("Segoe UI", -round(38 * sc), "bold")))
        self.add("ui", cv.create_text(W / 2, 0.098 * H, text=SUBTITLE, fill="#a5acbe",
                                      font=("Segoe UI", -round(18 * sc))))
        self.add("ui", cv.create_line(W / 2 - 130 * sc, 0.125 * H, W / 2 + 130 * sc, 0.125 * H,
                                      fill="#3c4252", width=1))
        self.counter = self.add("ui", cv.create_text(W - 24 * sc, H - 18 * sc, anchor="se",
                                                     fill="#8c92a2", text="",
                                                     font=("Consolas", -round(17 * sc))))
        self.status = self.add("ui", cv.create_text(20 * sc, H - 18 * sc, anchor="sw",
                                                    fill="#4a5060",
                                                    text="Space: replay   S: save HD   Esc: quit",
                                                    font=("Segoe UI", -round(12 * sc))))

        # الرأس المضيء
        self.head = [self.add("head", cv.create_oval(0, 0, 0, 0, width=0, fill=c))
                     for c in ("#2a2a33", "#77777f", "#d8d8e0", "#ffffff")]
        self.head_r = [15 * sc, 9 * sc, 5.5 * sc, 3.2 * sc]

        root.bind("<space>", lambda e: self.restart())
        root.bind("<Escape>", lambda e: root.destroy())
        root.bind("<s>", lambda e: self.save_hd(N if self.i >= N else self.i))
        root.bind("<S>", lambda e: self.save_hd(N if self.i >= N else self.i))

        self.job = None
        self.restart()

    # ---- helpers
    def add(self, layer, item):
        self.cv.tag_lower(item, self.marker[layer])
        return item

    def restart(self):
        if self.job:
            self.root.after_cancel(self.job)
        self.cv.delete("trail")
        self.i = 0
        self.saved = False
        self.cv.itemconfigure(self.status, text="Space: replay   S: save HD   Esc: quit")
        self.job = self.root.after(300, self.tick)

    def draw_step(self, i):
        cv, g, sc = self.cv, self.g, self.sc
        pts = g.seg(i, SUB)
        flat = [c for p in pts for c in p]
        k = i + 0.5
        opts = dict(capstyle=tk.ROUND, joinstyle=tk.ROUND, smooth=True, tags="trail")
        if i % RAY_EVERY == 0:
            self.add("rays", cv.create_line(g.cx, g.cy, *pts[-1], fill=hexc(rgb(k, 0.30)),
                                            width=1, tags="trail"))
        self.add("glow", cv.create_line(*flat, fill=hexc(rgb(k, 0.20)), width=11 * sc, **opts))
        self.add("mid", cv.create_line(*flat, fill=hexc(rgb(k, 0.50)), width=5.5 * sc, **opts))
        self.add("core", cv.create_line(*flat, fill=hexc(rgb(k, 1.0, 0.30)), width=2.2 * sc, **opts))
        if i % DOT_EVERY == 0:
            x, y = pts[0]
            r = 3.4 * sc
            self.add("dots", cv.create_oval(x - r, y - r, x + r, y + r, width=0,
                                            fill=hexc(rgb(k, 1.0, 0.25)), tags="trail"))
            r = 1.4 * sc
            self.add("dots", cv.create_oval(x - r, y - r, x + r, y + r, width=0,
                                            fill="#ffffff", tags="trail"))

    def tick(self):
        for _ in range(STEPS_PER_FRAME):
            if self.i >= N:
                break
            self.draw_step(self.i)
            self.i += 1

        x, y = self.g.px(curve(self.i))
        for item, r in zip(self.head, self.head_r):
            self.cv.coords(item, x - r, y - r, x + r, y + r)
        self.cv.itemconfigure(self.counter, text=f"i = {self.i:4d}/{N}")

        # لمعان النجوم
        for _ in range(4):
            sid, v = random.choice(self.stars)
            f = v * random.uniform(0.4, 1.5)
            self.cv.itemconfigure(sid, fill=hexc((f, f, min(1, f + 0.08))))

        if self.i < N:
            self.job = self.root.after(FRAME_MS, self.tick)
        else:
            self.job = None
            if not self.saved:
                self.root.after(600, lambda: self.save_hd(N))

    def save_hd(self, upto):
        if upto <= 0:
            return
        self.cv.itemconfigure(self.status, text="Rendering HD image...")
        self.root.update_idletasks()
        try:
            path = render_hd(upto=upto)
            self.saved = True
            msg = f"Saved: {os.path.basename(path)}   |   Space: replay   Esc: quit"
        except ImportError:
            msg = "Install Pillow for HD export:  pip install pillow"
        self.cv.itemconfigure(self.status, text=msg)


def main():
    if "--hd" in sys.argv:
        print("saved", render_hd())
        return
    if sys.platform == "win32":                      # خطوط حادة على شاشات الدقة العالية
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
