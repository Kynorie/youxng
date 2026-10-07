# YouXNG

YouXNG is a simple video downloader that runs on your own computer. It works with YouTube and Twitter (X). It uses [yt-dlp](https://github.com/yt-dlp/yt-dlp) to do the downloading, and it shows a clean page in your web browser.

Nothing is sent to any server of ours. The app only runs on your machine, and only you can open it.

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

Next time, you only need to run `source venv/bin/activate` and then `python youxng.py` from the project folder.

## How to use it

1. Open the **Home** tab.
2. Click the platform button next to the arrow button. Choose **YouTube** or **Twitter**.
3. Paste a link into the box and press Enter, or click the arrow button.
4. When you see "Download ready!", click **Download MP4** or **Download MP3**.

## Platforms

YouXNG checks that your link matches the platform you picked. If it does not match, you will see an error.

- **YouTube**: links with `youtube.com/` or `youtu.be`
- **Twitter (X)**: links with `twitter.com/` or `x.com/`

Twitter links only work for posts that have a video. Some posts, like protected or age-restricted ones, may not download because X can ask for a login.

## Tabs

- **Home**: the main downloader.
- **Updates**: checks if there is a new version of YouXNG, and a new version of yt-dlp.
- **Settings**: dark mode, default platform, hardcoded resolution, hardcoded type, file name, and sidebar gap.
- **Store**: a preview of YouXNG+. It is not for sale yet.

## Keeping yt-dlp up to date

YouTube and Twitter change often, so yt-dlp needs updates to keep working. If downloads stop working, update it:

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
- The platform you pick in the dropdown is only kept until you close the page. To change it for good, use the **Default Platform** setting.
- The app only listens on `127.0.0.1`, so other devices on your network cannot reach it.
- Only download videos that you have the right to download. Do not share other people's videos without their permission.
