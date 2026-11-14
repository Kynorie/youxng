import json, os, re, shutil, tempfile, threading, time, uuid, webbrowser
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import yt_dlp
from flask import Flask, jsonify, request, send_file, send_from_directory
from yt_dlp.version import __version__ as YTDLP_VERSION

VERSION = "0.6.0"
REPO = "kynorie/youxng"
HOST, PORT = "127.0.0.1", 3003

app = Flask(__name__)
JOBS, FILES = {}, {}
TTL = 1800  # seconds a finished file stays available


PLATFORMS = {
    "youtube": ("youtu.be", "youtube.com"),
    "twitter": ("twitter.com", "x.com"),
    "tiktok": ("tiktok.com",),
    "reddit": ("reddit.com", "redd.it"),
    "soundcloud": ("soundcloud.com",),
    "twitch": ("twitch.tv",),
    "bluesky": ("bsky.app",),
    "newgrounds": ("newgrounds.com",),
}
NAMES = {
    "youtube": "YouTube", "twitter": "Twitter", "tiktok": "TikTok", "reddit": "Reddit",
    "soundcloud": "SoundCloud", "twitch": "Twitch", "bluesky": "Bluesky", "newgrounds": "Newgrounds",
}
VIDEO_FORMATS = ("mp4", "mkv")
AUDIO_CODECS = {"mp3": "mp3", "ogg": "vorbis", "m4a": "m4a", "flac": "flac", "wav": "wav", "opus": "opus"}


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
    formats = d.get("formats") or []
    audio_only = not heights and bool(formats) and all(f.get("vcodec") == "none" for f in formats)
    return jsonify(title=d.get("title") or "video", heights=heights, url=url, audio_only=audio_only)


def run_job(jid, url, fmt, res, j):
    job = JOBS[jid]
    tmp = tempfile.mkdtemp(prefix="youxng-")
    parts = {}

    def hook(d):
        if d.get("status") not in ("downloading", "finished"):
            return
        if d["status"] == "finished":
            frac = 1
        else:
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            if total:
                frac = (d.get("downloaded_bytes") or 0) / total
            elif d.get("fragment_count"):
                frac = (d.get("fragment_index") or 0) / d["fragment_count"]
            else:
                frac = 0
        parts[d.get("filename") or ""] = min(frac, 1)
        streams = len((d.get("info_dict") or {}).get("requested_formats") or []) or 1
        pct = int(sum(parts.values()) / max(streams, len(parts)) * 100)
        job["pct"] = max(job["pct"], min(99, pct))

    opts = {"quiet": True, "noplaylist": True, "progress_hooks": [hook],
            "outtmpl": os.path.join(tmp, "out.%(ext)s")}
    if fmt in AUDIO_CODECS:
        opts.update(format="bestaudio/best", postprocessors=[
            {"key": "FFmpegExtractAudio", "preferredcodec": AUDIO_CODECS[fmt], "preferredquality": "192"}])
    else:
        c = f"[height<={int(res)}]" if res.isdigit() else ""
        pick = f"bv*{c}+ba/b{c}" if fmt == "mkv" else f"bv*{c}[ext=mp4]+ba[ext=m4a]/bv*{c}+ba/b{c}"
        opts.update(format=pick, merge_output_format=fmt)
    try:
        with yt_dlp.YoutubeDL(opts) as y:
            d = y.extract_info(url, download=True)
        f = next(x for x in os.listdir(tmp) if x.startswith("out."))
    except Exception:
        shutil.rmtree(tmp, ignore_errors=True)
        job.update(status="error", error="Download failed. Is ffmpeg installed?")
        return
    title = re.sub(r'[\\/:*?"<>|]+', "", d.get("title") or "").strip()
    custom = re.sub(r'[\\/:*?"<>|\x00-\x1f]+', "", str(j.get("custom") or "")).strip(" .")[:100]
    base = custom or (title if j.get("name") == "title" and title else "youxng-video")
    token = uuid.uuid4().hex
    FILES[token] = (os.path.join(tmp, f), f"{base}.{f.rsplit('.', 1)[-1]}", tmp, time.time())
    job.update(status="done", pct=100, token=token)


@app.post("/api/prepare")
def prepare():
    j = request.json or {}
    platform = get_platform(j.get("platform"))
    url = clean_url(j.get("url"), platform)
    if not url:
        return jsonify(error=f"Please add a {NAMES[platform]} link!"), 400
    fmt, res = str(j.get("fmt", "mp4")).lower(), str(j.get("res", "best"))
    if fmt not in VIDEO_FORMATS and fmt not in AUDIO_CODECS:
        fmt = "mp4"
    jid = uuid.uuid4().hex
    JOBS[jid] = dict(status="running", pct=0, ts=time.time())
    threading.Thread(target=run_job, args=(jid, url, fmt, res, j), daemon=True).start()
    return jsonify(job=jid)


@app.get("/api/progress/<jid>")
def progress(jid):
    job = JOBS.get(jid)
    if not job:
        return jsonify(error="Expired"), 404
    return jsonify(status=job["status"], pct=job["pct"], token=job.get("token"), error=job.get("error"))


@app.get("/api/file/<token>")
def file(token):
    f = FILES.get(token)
    if not f:
        return "Expired", 404
    return send_file(f[0], as_attachment=True, download_name=f[1])


CHECKS = {
    "ffmpeg": lambda: bool(shutil.which("ffmpeg")),
    "ffprobe": lambda: bool(shutil.which("ffprobe")),
    "yt-dlp": lambda: callable(getattr(yt_dlp, "YoutubeDL", None)),
}


@app.get("/api/check/<name>")
def check(name):
    fn = CHECKS.get(name)
    if not fn:
        return jsonify(error="Unknown check"), 404
    return jsonify(ok=fn())


def sweep():
    while True:
        time.sleep(60)
        now = time.time()
        for token, f in list(FILES.items()):
            if now - f[3] > TTL:
                FILES.pop(token, None)
                shutil.rmtree(f[2], ignore_errors=True)
        for k, job in list(JOBS.items()):
            if now - job["ts"] > TTL:
                JOBS.pop(k, None)


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
    threading.Thread(target=sweep, daemon=True).start()
    threading.Timer(1, lambda: webbrowser.open(f"http://{HOST}:{PORT}")).start()
    app.run(HOST, PORT)
