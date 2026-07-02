# ⬇️ Modern YouTube Downloader

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![UI Library](https://img.shields.io/badge/GUI-CustomTkinter-darkblue.svg)](https://github.com/TomSchimansky/CustomTkinter)
[![Backend Engine](https://img.shields.io/badge/Engine-yt--dlp-red.svg)](https://github.com/yt-dlp/yt-dlp)
[![Tests Status](https://img.shields.io/badge/Tests-17%20Passed-brightgreen.svg)](test_youtube_downloader.py)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A clean, modern, and high-performance desktop application for downloading high-quality videos and audio seamlessly. Built with Python, **CustomTkinter** for a beautiful native dark/light mode UI, and powered by **yt-dlp** for robust stream extraction.

---

## 💡 Why This Project Exists

We've all been there: you need to download a video for an offline presentation, a flight, or a personal backup, and you end up on a sketchy website filled with pop-up ads, fake download buttons, and slow speed throttles. 

This downloader was created as a **human-centric, secure alternative**:
*   **Zero Ads or Bloat:** Runs entirely on your machine.
*   **Privacy-First:** Your data and downloads never touch a third-party server besides YouTube.
*   **Respects Your System:** Light on resources, robust with errors, and fully controllable.
*   **Made to Last:** Uses a self-contained configuration file to remember your settings and automatically handles platform differences.

---

## ✨ Features at a Glance

*   **⚡ Smart Link Analysis:** Inspect video metadata (Title, Channel, and Duration) before committing to a download.
*   **⏯️ Playback-Style Controls:** Real-time **Pause**, **Resume**, and **Stop/Cancel** download actions mapped to thread-safe execution events.
*   **📦 Output Quality Options:**
    *   **Highly Compatible (MP4 - 1080p Max):** High-definition video with pristine audio merging.
    *   **Audio Only (MP3):** Extracts pure 192kbps audio for podcasts, audiobooks, or music.
*   **🛡️ Playlist Protection:** Toggles full playlist downloads with an intelligent **10-second request delay** between tracks to safeguard your IP from rate limits.
*   **🛠️ Embedded Terminal Log:** Tracks execution live, displaying warnings, errors, and system status directly inside the GUI.
*   **💾 State Persistence:** Remembers your download directory, preferred quality, auto-clear choice, and playlist settings across app sessions.
*   **🧩 Intelligently Located FFmpeg:** Discovers your FFmpeg installation automatically, whether it is in your system PATH or simply placed next to the script.

---

## 🚀 Quick Start

### 📋 Prerequisites
*   **Python 3.8 or higher**
*   **FFmpeg** (Required for audio/video merging and MP3 extraction)

### 💾 Installation

1.  **Clone the Repository:**
2.  **Set Up a Virtual Environment (Highly Recommended):**
    ```bash
    python -m venv .venv
    # On Windows:
    .venv\Scripts\activate
    # On macOS/Linux:
    source .venv/bin/activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(If a `requirements.txt` is not provided, you can install the main packages directly: `pip install customtkinter yt-dlp`)*

4.  **Run the Application:**
    ```bash
    python youtube_downloader.py
    ```

---

## ⚙️ Setting Up FFmpeg (Highly Recommended)

Because YouTube serves high-resolution video (1080p+) and high-quality audio in separate streams, **FFmpeg is required** to merge them back into a single high-quality file, as well as to convert audio tracks to MP3s.

The application has a smart auto-detector that makes setting this up painless!

### 🪟 Windows (Easiest Way)
1. Download a pre-built package from [BtbN FFmpeg Releases](https://github.com/BtbN/FFmpeg-Builds/releases) (look for `ffmpeg-master-latest-win64-gpl.zip`).
2. Open the downloaded `.zip` file, navigate inside the `bin` folder, and locate `ffmpeg.exe`.
3. Drag and drop `ffmpeg.exe` **into the exact same folder** as `youtube_downloader.py`.
4. Relaunch the application. The status indicator will turn green: **✅ FFmpeg: Active**.

### 🍎 macOS
Install via [Homebrew](https://brew.sh/):
```bash
brew install ffmpeg
```

### 🐧 Linux
Install via your native package manager:
```bash
sudo apt update && sudo apt install ffmpeg
```

---

## 🧪 Testing and Quality Control

This project is backed by a robust and fully-mocked test suite. Because it uses sophisticated GUI patches, **you can run these tests in headless environments** (such as GitHub Actions or remote CI/CD pipelines) without getting "display/no screen" errors.

To run the 17 unit tests:
```bash
python -m unittest test_youtube_downloader.py
```

### What the tests cover:
*   **Configuration Handling:** Fallback states, JSON reads/writes, and directory verification.
*   **Environment Integration:** Intelligent FFmpeg path detection on multiple operating systems (Windows & Unix).
*   **Interactive Mechanics:** Clipboard interaction (Paste/Copy/Clear), responsive buttons, and event state triggers.
*   **yt-dlp Parameter Passing:** Formatting configurations for playlists, anti-ban timers, and specific formats.
*   **Threading Hooks:** Progress bar percentage calculation, speed/ETA mapping, and graceful cancellation.

---

## 🛠️ Tech Stack & Architecture

*   **GUI Engine:** [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) (dynamic dark/light mode, custom modern widgets).
*   **Engine Core:** [yt-dlp](https://github.com/yt-dlp/yt-dlp) (the most reliable and up-to-date fork of the original youtube-dl package).
*   **Threading Model:** Heavy network requests and info fetching are spawned off the Main GUI Thread using Python's native `threading` library, maintaining a locked 60FPS UI response rate.
*   **Thread Synchronization:** Uses `threading.Event()` to securely pause and signal stop states to deep `yt-dlp` download cycles.

---

## 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information (or feel free to use this code as you wish for personal projects!).

---

