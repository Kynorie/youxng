# YouXNG

YouXNG is a simple YouTube video downloader that runs on your own computer. It uses [yt-dlp](https://github.com/yt-dlp/yt-dlp) to do the downloading, and it shows a clean page in your web browser.

Nothing is sent to any server of ours. The app only runs on your machine, and only you can open it.

## Features

- Paste a YouTube link and download the video as MP4 or MP3
- Pick a video resolution, or set one in the settings
- Save files with the video title or with a fixed name
- Dark mode, and a sidebar you can resize by dragging its edge
- Update checker for YouXNG and yt-dlp

## What you need

- Python 3.9 or newer
- [ffmpeg](https://ffmpeg.org/) (needed to join video and audio, and to make MP3 files)
- A web browser

## Installation

**Step 1: Get the code**

```
git clone https://github.com/kynorie/youxng.git
cd youxng
```

**Step 2: Install ffmpeg**

On Debian or Ubuntu: (APT)

```
sudo apt install ffmpeg
```

On Arch: (Pacman)

```
sudo pacman -S ffmpeg
```

On Fedora: (Dnf)

```
sudo dnf install ffmpeg
```

**Step 3: Install the Python packages**

It is best to use a virtual environment so nothing else on your system is changed:

```
python3 -m venv venv
source venv/bin/activate
pip install flask yt-dlp
```

## Running

Start the app:

```
python youxng.py
```

Your browser should open by itself. If it does not, go to:

```
http://127.0.0.1:3003
```

To stop the app, go back to the terminal and press `Ctrl+C`.

## How to use it

1. Open the **Home** tab.
2. Paste a YouTube link into the box and press Enter, or click the arrow button.
3. When you see "Download ready!", click **Download MP4** or **Download MP3**.

## Tabs

- **Home**: the main downloader.
- **Updates**: checks if there is a new version of YouXNG, and a new version of yt-dlp.
- **Settings**: dark mode, hardcoded resolution, hardcoded type, file name, and sidebar gap.
- **Store**: a preview of YouXNG+. It is not for sale yet.

## Keeping yt-dlp up to date

YouTube changes often, so yt-dlp needs updates to keep working. If downloads stop working, update it:

```
pip install -U yt-dlp
```

## Files

```
youxng/
  youxng.py          the backend (Flask and yt-dlp)
  static/
    index.html       the whole web page
```

## Good to know

- Your settings are saved in your browser, not in a file.
- The app only listens on `127.0.0.1`, so other devices on your network cannot reach it.
- Only download videos that you have the right to download.
