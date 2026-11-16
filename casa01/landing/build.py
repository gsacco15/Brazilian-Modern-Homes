"""Build the Casa Pátio early-list landing page.

    python3 casa01/landing/build.py      ->  casa01/landing/site/   (deploy this folder)

page.html is the page body (also used as-is for the Claude preview). This script wraps it in a
full HTML document with social-sharing tags and the optional ad pixels from config.json, and
writes phone-sized images from the renders.
"""
import html
import json
import os
import re

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
CASA = os.path.dirname(HERE)
SITE = os.path.join(HERE, "site")
IMG = os.path.join(SITE, "img")
RENDERS = os.path.join(CASA, "renders")
PANO = os.path.join(CASA, "lookbook", "web", "pano")
STILLS = ["street", "street_dusk", "entry", "courtyard", "interior", "kitchen", "bath", "veranda"]

DESCRIPTION = ("Casa Pátio: a Brazilian modern courtyard house for your Austin lot. Texas limestone, cedar "
               "and a concrete cobogó screen under one long roof. Join the early list.")

META_PIXEL = """<script>!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');fbq('init','__ID__');fbq('track','PageView');</script>"""
X_PIXEL = """<script>!function(e,t,n,s,u,a){e.twq||(s=e.twq=function(){s.exe?s.exe.apply(s,arguments):s.queue.push(arguments);},s.version='1.1',s.queue=[],u=t.createElement(n),u.async=!0,u.src='https://static.ads-twitter.com/uwt.js',a=t.getElementsByTagName(n)[0],a.parentNode.insertBefore(u,a))}(window,document,'script');twq('config','__ID__');</script>"""
RESET = ("*,*::before,*::after{box-sizing:border-box}:root{padding-top:env(safe-area-inset-top,0px);"
         "padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0}img{max-width:100%}[hidden]{display:none!important}"
         "html{scroll-behavior:smooth}")


def jpg(src, dst, width, quality):
    im = Image.open(src).convert("RGB")
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(dst, quality=quality, optimize=True, progressive=True)


def images():
    os.makedirs(IMG, exist_ok=True)
    for k in STILLS:
        src = os.path.join(RENDERS, f"{k}.png")
        jpg(src, os.path.join(IMG, f"{k}-1600.jpg"), 1600, 80)
        jpg(src, os.path.join(IMG, f"{k}-800.jpg"), 800, 78)
    # 2560 px panoramas: sharp enough on a phone, small enough to load on cellular
    for k in ("patio", "room"):
        jpg(os.path.join(PANO, f"{k}.jpg"), os.path.join(IMG, f"pano-{k}.jpg"), 2560, 80)
    # 1200x630 link preview for Instagram, X, iMessage
    im = Image.open(os.path.join(RENDERS, "street.png")).convert("RGB")
    w, h = im.size
    ch = round(w / 1.905)
    top = max(0, min(h - ch, round(h * 0.06)))
    im.crop((0, top, w, top + ch)).resize((1200, 630), Image.LANCZOS).save(
        os.path.join(IMG, "og.jpg"), quality=84, optimize=True, progressive=True)


def build():
    cfg = json.load(open(os.path.join(HERE, "config.json")))
    page = open(os.path.join(HERE, "page.html")).read()
    title = re.search(r"<title>(.*?)</title>", page, re.S).group(1)
    style = re.search(r"<style>.*?</style>", page, re.S).group(0)
    links = "".join(re.findall(r"<link [^>]+>", page))
    body = re.sub(r"<title>.*?</title>|<meta name=\"claude:[^>]+>|<link [^>]+>|<style>.*?</style>", "", page, flags=re.S).strip()
    site = cfg.get("site_url", "").rstrip("/")
    og_img = f"{site}/img/og.jpg" if site else "img/og.jpg"
    browser_cfg = {"formEndpoint": cfg.get("form_endpoint", ""), "xLeadEventId": cfg.get("x_lead_event_id", "")}
    pixels = ""
    if cfg.get("meta_pixel_id"):
        pixels += META_PIXEL.replace("__ID__", cfg["meta_pixel_id"])
    if cfg.get("x_pixel_id"):
        pixels += X_PIXEL.replace("__ID__", cfg["x_pixel_id"])
    t, d = html.escape(title), html.escape(DESCRIPTION)
    head = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        f"<title>{t}</title><meta name=\"description\" content=\"{d}\">"
        '<meta name="theme-color" content="#1d2520">'
        f'<meta property="og:type" content="website"><meta property="og:title" content="Casa Pátio · Brazilian Modern Homes">'
        f'<meta property="og:description" content="{d}"><meta property="og:image" content="{og_img}">'
        + (f'<meta property="og:url" content="{site}/">' if site else "")
        + '<meta name="twitter:card" content="summary_large_image">'
        f'<meta name="twitter:title" content="Casa Pátio · Brazilian Modern Homes"><meta name="twitter:description" content="{d}">'
        f'<meta name="twitter:image" content="{og_img}">'
        f"<style>{RESET}</style>{links}"
        f"<script>window.BMH_CONFIG={json.dumps(browser_cfg)};</script>{pixels}{style}</head><body>"
    )
    os.makedirs(SITE, exist_ok=True)
    open(os.path.join(SITE, "index.html"), "w").write(head + body + "</body></html>")
    print("wrote", os.path.join(SITE, "index.html"))


if __name__ == "__main__":
    images()
    build()
