# ⬇️ YouTube Downloader

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![UI Library](https://img.shields.io/badge/GUI-CustomTkinter-darkblue.svg)](https://github.com/TomSchimansky/CustomTkinter)
[![Backend Engine](https://img.shields.io/badge/Engine-yt--dlp-red.svg)](https://github.com/yt-dlp/yt-dlp)
[![Tests Status](https://img.shields.io/badge/Tests-Passed-brightgreen.svg)](test_youtube_downloader.py)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A stunning, localized, and human-friendly desktop media downloader. Built with Python, styled with **CustomTkinter** for a gorgeous native dark/light mode experience, and powered by **yt-dlp** for robust, high-speed stream extraction.

---

## 💡 The Story Behind the Project

We’ve all been there: you need an offline copy of a lecture for a flight, a video for a school presentation, or simply want to archive your favorite video before it disappears from the internet. 

In search of a simple download, you end up on sketchy web converters. They bombard you with flashing advertisements, redirect you to suspicious betting sites, try to trick you into downloading malware with fake "Download" buttons, and throttle your speed to a crawl.

**We wanted something better. Something we’d be proud to show our families.**

This YouTube Downloader is designed to be a **human-centric, secure, and respectful desktop experience**:
*   **Zero Ads, Zero Bloat:** It runs entirely on your machine.
*   **Privacy-First:** Your data never touches a third-party server besides YouTube.
*   **Complete Control:** Real-time pause, resume, and cancellation mechanics that actually work.
*   **Global Access:** Fully translated and localized into **11 major world languages** out of the box.

---

## ✨ Features Designed for You

*   **⚡ Peek Before Downloading:** Input a link and click **Analyze Link** to safely view the video title, channel, and exact duration before initiating any file transfers.
*   **⏯️ True Playback-Style Thread Controls:** Need to free up bandwidth or pause because your internet is slow? Click **Pause** to suspend the active transfer and **Resume** whenever you're ready. Click **Stop** to cancel cleanly without leaving half-downloaded junk or freezing the application.
*   **📦 Beautiful Media Formats:**
    *   **Highly Compatible Video:** Merges high-definition video track and high-fidelity audio track into a single standalone `.mp4` file (up to 1080p).
    *   **Audio Only:** Extracts crystal-clear `.mp3` audio tracks—ideal for offline podcasts, audiobooks, lectures, and music.
*   **🛡️ Playlist Protection Mode:** Downloading a whole series? The application features an intelligent safety throttle that introduces a **10-second pause between playlist tracks**. This shields your IP address from sudden rate limits or temporary IP bans by YouTube.
*   **🛠️ Live Collapsible Terminal Log:** Want to see exactly what’s happening? Click the *Show Live Log Terminal* switch to expand a built-in terminal log that tracks yt-dlp operations in real-time. Uncheck it to keep your interface clean and simple.
*   **💾 Automatic State Persistence:** Your preference for Save Destination, preferred quality, auto-clear preference, language, theme (Dark/Light), and log visibility are saved automatically in `ytdl_config.json` and reloaded the next time you open the app.

---

## 🌍 Speaking Your Language

We believe technology should be accessible. The interface has been completely hand-translated into **11 major world languages**. Changing languages instantly reorganizes and re-labels every button, prompt, tool-tip, and checkbox:

*   🇺🇸 **English**
*   🇧🇬 **Български** (Bulgarian)
*   🇷🇺 **Русский** (Russian)
*   🇫🇷 **Français** (French)
*   🇮🇹 **Italiano** (Italian)
*   🇩🇪 **Deutsch** (German)
*   🇪🇸 **Español** (Spanish)
*   🇯🇵 **日本語** (Japanese)
*   🇰🇷 **한국어** (Korean)
*   🇨🇳 **简体中文** (Simplified Chinese)
*   🇮🇳 **हिन्दी** (Hindi)

---

## 🚀 Quick Start Guide

Getting started is quick and easy!

### 1. Prerequisites
Make sure you have **Python 3.8** (or higher) installed on your system.

### 2. Setup standard virtual environment
We highly recommend setting up a virtual environment to keep your global Python installation clean:

> [!NOTE]
> # Clone or navigate to the project directory
```bash
> cd "Youtube Downloader"
```
> # Create a virtual environment
 ```bash
 python -m venv .venv
 ```
> # Activate the virtual environment:
> # On Windows:
```bash
.venv\Scripts\activate
 ```
> # On macOS/Linux:
```bash
source .venv/bin/activate
```

### 3. Install Dependencies
Install the required packages. The application depends primarily on `customtkinter` (for modern visuals) and `yt-dlp` (the heavy-lifting download engine):

```bash
pip install customtkinter yt-dlp
```

### 4. Launch the App
Run the main script to bring up the interface:
```bash
python youtube_downloader.py
```

---

## ⚙️ The Stress-Free Guide to FFmpeg

### Why do I need FFmpeg?
YouTube serves high-resolution video streams (1080p+) and high-quality audio streams as separate files to save bandwidth. To bring you the best possible quality, the application downloads both streams separately. **FFmpeg is the helper engine** that stitches them back together into a single, high-definition MP4 file, and converts audio streams to MP3s.

Our application features an **intelligent auto-detection engine** to make setting this up a breeze.

<details>
<summary><b>🪟 Windows Setup (Easiest Way - Drag and Drop)</b></summary>
<br>

1. Download a pre-built static package of FFmpeg (e.g., from [BtbN FFmpeg Releases](https://github.com/BtbN/FFmpeg-Builds/releases) — look for a `.zip` file ending with `-win64-gpl.zip`).
2. Open the downloaded `.zip` file, navigate inside the `bin` folder, and locate `ffmpeg.exe`.
3. **Drag and drop `ffmpeg.exe` directly into the project folder** (right next to `youtube_downloader.py`).
4. Relaunch the application. The configuration section will light up with:  
   `✅ FFmpeg: Active (MP4/MP3 Enabled)`
</details>

<details>
<summary><b>🍎 macOS Setup</b></summary>
<br>

Install via [Homebrew](https://brew.sh/):
```bash
brew install ffmpeg
```
Once installed, our application will automatically detect FFmpeg in your system path and activate.
</details>

<details>
<summary><b>🐧 Linux Setup</b></summary>
<br>

Install via your native package manager:
```bash
# Debian/Ubuntu
sudo apt update && sudo apt install ffmpeg

# Fedora/RHEL
sudo dnf install ffmpeg
```
Once installed, our application will automatically detect FFmpeg in your system path and activate.
</details>

---

## 🧠 Under the Hood (For the Curious Developer)

This application is built with clean separation of concerns and robust technical architecture:

1.  **Multi-threaded UI Loop:** Heavily intensive tasks—like resolving stream metadata and running high-bandwidth downloads—are fully separated from the main CustomTkinter GUI thread. This guarantees a locked **60 FPS responsive UI**, preventing standard Tkinter "Not Responding" freeze behaviors.
2.  **Thread Synchronization via Events:** Python's native `threading.Event` acts as the sync mechanism. When a user clicks "Pause" or "Stop", thread-safe signals are passed directly into the deep execution loops of `yt-dlp`, pausing or halting bytes cleanly.
3.  **Encapsulated Localization:** High-volume string variables are securely structured in `languages.py` in a key-matched format. An exhaustive unit test verifies key parity across languages, guaranteeing that no language selection can trigger a `KeyError` at runtime.
4.  **Graceful Fallbacks:** If FFmpeg is missing, the app doesn't crash or block you. It gracefully adjusts the fallback extraction formats to stream standard formats (`best` single-file streams), meaning you can still download standard-definition media seamlessly!

---

## 🧪 Quality and Reliability

We take code health and reliability seriously. The project is backed by a fully mocked test suite containing exhaustive unit tests. 

Importantly, **all GUI visual tests are engineered to dynamically detect display servers**—if no display screen is found (such as in remote SSH or headless GitHub CI/CD pipelines), the suite skips the graphical renders while keeping core downloader logic fully tested!

To run the test suite:
```bash
python -m unittest test_youtube_downloader.py
```

### What the test suite verifies:
*   **Dictionary Integrity:** Full key consistency matches across all 11 languages to prevent runtime crash triggers.
*   **yt-dlp Parameter Integrity:** Correct option structures generated for audio (MP3 extracts, postprocessor definitions) and high-fidelity video formats.
*   **Environment Integrations:** Robust multi-platform scanning logic for discovering localized and system-level FFmpeg binaries.
*   **Config Resilience:** File-read error handling and safe, reliable JSON configuration writes.

---

## 🤝 Contributing

This project is open-source and welcomes community suggestions and improvements!

1. **Fork** the Repository.
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`).
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to your Branch (`git push origin feature/AmazingFeature`).
5. Open a **Pull Request** and let's discuss!

---

## 💖 Heartfelt Credits

This tool was only made possible thanks to the tireless work of developers maintaining these world-class open-source projects:

*   **TomSchimansky** for [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter), bringing Tkinter into the modern era with sleek, responsive dark/light widgets.
*   **The yt-dlp Maintainers** for [yt-dlp](https://github.com/yt-dlp/yt-dlp), the absolute gold standard in stream parsing and stream-extracting engines.
*   **The FFmpeg Team** for [FFmpeg](https://ffmpeg.org/), the indispensable swiss army knife of audio/video processing.

---

## 📜 License

Distributed under the **MIT License**. Use this code for learning, personal use, or customized scripting as you see fit! See the `LICENSE` file for more details.
