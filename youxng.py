import json, os, re, shutil, tempfile, threading, uuid, webbrowser
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import yt_dlp
from flask import Flask, jsonify, request, send_file, send_from_directory
from yt_dlp.version import __version__ as YTDLP_VERSION

VERSION = "0.4.0"
REPO = "kynorie/youxng"
HOST, PORT = "127.0.0.1", 3003

app = Flask(__name__)
JOBS = {}


PLATFORMS = {
    "youtube": ("youtu.be", "youtube.com"),
    "twitter": ("twitter.com", "x.com"),
    "tiktok": ("tiktok.com",),
    "reddit": ("reddit.com", "redd.it"),
}
NAMES = {"youtube": "YouTube", "twitter": "Twitter", "tiktok": "TikTok", "reddit": "Reddit"}


def get_platform(value):
    return value if value in PLATFORMS else "youtube"


def clean_url(raw, platform="youtube"):
    raw = (raw or "").strip()
    if not re.match(r"^https?://", raw, re.I):
        raw = "https://" + raw
    host = (urlparse(raw).hostname or "").lower()
    ok = any(host == d or host.endswith("." + d) for d in PLATFORMS[get_platform(platform)])
    return raw if ok else None


def fetch_json(url):
    with urlopen(Request(url, headers={"User-Agent": "YouXNG"}), timeout=8) as r:
        return json.load(r)


def is_newer(latest, current):
    nums = lambda v: [int(x) for x in re.findall(r"\d+", v)]
    return nums(latest) > nums(current)


@app.get("/")
def index():
    return send_from_directory(app.root_path + "/static", "index.html")


@app.post("/api/info")
def info():
    j = request.json or {}
    platform = get_platform(j.get("platform"))
    url = clean_url(j.get("url"), platform)
    if not url:
        return jsonify(error=f"Please add a {NAMES[platform]} link!"), 400
    try:
        with yt_dlp.YoutubeDL({"quiet": True, "noplaylist": True}) as y:
            d = y.extract_info(url, download=False)
    except Exception:
        return jsonify(error="Couldn't find that video."), 400
    heights = sorted({f["height"] for f in d.get("formats", [])
                      if f.get("height") and f.get("vcodec") != "none"}, reverse=True)
    return jsonify(title=d.get("title") or "video", heights=heights, url=url)


@app.post("/api/prepare")
def prepare():
    j = request.json or {}
    platform = get_platform(j.get("platform"))
    url = clean_url(j.get("url"), platform)
    if not url:
        return jsonify(error=f"Please add a {NAMES[platform]} link!"), 400
    kind, res = ("mp3" if j.get("type") == "mp3" else "mp4"), str(j.get("res", "best"))
    tmp = tempfile.mkdtemp(prefix="youxng-")
    opts = {"quiet": True, "noplaylist": True, "outtmpl": os.path.join(tmp, "out.%(ext)s")}
    if kind == "mp3":
        opts.update(format="bestaudio/best", postprocessors=[
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}])
    else:
        c = f"[height<={int(res)}]" if res.isdigit() else ""
        opts.update(format=f"bv*{c}[ext=mp4]+ba[ext=m4a]/bv*{c}+ba/b{c}", merge_output_format="mp4")
    try:
        with yt_dlp.YoutubeDL(opts) as y:
            d = y.extract_info(url, download=True)
        f = os.listdir(tmp)[0]
    except Exception:
        shutil.rmtree(tmp, ignore_errors=True)
        return jsonify(error="Download failed. Is ffmpeg installed?"), 500
    title = re.sub(r'[\\/:*?"<>|]+', "", d.get("title") or "").strip()
    base = title if j.get("name") == "title" and title else "youxng-video"
    token = uuid.uuid4().hex
    JOBS[token] = (os.path.join(tmp, f), f"{base}.{f.rsplit('.', 1)[-1]}", tmp)
    return jsonify(token=token)


@app.get("/api/file/<token>")
def file(token):
    job = JOBS.pop(token, None)
    if not job:
        return "Expired", 404
    path, name, tmp = job
    r = send_file(path, as_attachment=True, download_name=name)
    r.call_on_close(lambda: shutil.rmtree(tmp, ignore_errors=True))
    return r


@app.get("/api/updates")
def updates():
    checks = {
        "app": (VERSION, lambda: fetch_json(f"https://api.github.com/repos/{REPO}/tags")[0]["name"]),
        "ytdlp": (YTDLP_VERSION, lambda: fetch_json("https://pypi.org/pypi/yt-dlp/json")["info"]["version"]),
    }
    out = {}
    for key, (cur, get) in checks.items():
        try:
            latest = get().lstrip("v")
            out[key] = dict(current=cur, latest=latest, new=is_newer(latest, cur))
        except Exception:
            out[key] = dict(current=cur, error=True)
    return jsonify(out)


if __name__ == "__main__":
    threading.Timer(1, lambda: webbrowser.open(f"http://{HOST}:{PORT}")).start()
    app.run(HOST, PORT)
