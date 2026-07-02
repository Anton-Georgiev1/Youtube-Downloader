import os
import sys
import shutil
import threading
from pathlib import Path
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import yt_dlp

# Set appearance and default color theme
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class YDLLogger:
    """Redirects yt-dlp logs directly to the application's text console."""
    def __init__(self, app):
        self.app = app

    def debug(self, msg):
        # Filter out repetitive download percentage lines to avoid spamming the console
        if "[download]" in msg and "%" in msg:
            return
        self.app.safe_log(msg)

    def info(self, msg):
        self.app.safe_log(msg)

    def warning(self, msg):
        self.app.safe_log(f"⚠️ Warning: {msg}")

    def error(self, msg):
        self.app.safe_log(f"❌ Error: {msg}")


class YouTubeDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window configuration
        self.title("⬇️ YouTube Media Downloader")
        self.geometry("750x800")
        self.minsize(650, 700)

        # Main variables
        self.url_var = ctk.StringVar()
        self.quality_var = ctk.StringVar(value="Best Quality")
        
        # Determine default download path (Downloads folder or current directory)
        downloads_path = str(Path.home() / "Downloads")
        if not os.path.exists(downloads_path):
            downloads_path = os.getcwd()
        self.path_var = ctk.StringVar(value=downloads_path)

        # Check for FFmpeg
        self.ffmpeg_available = shutil.which("ffmpeg") is not None

        # Build GUI
        self.setup_ui()

        # Log initial environment info
        self.log_initial_status()

    def setup_ui(self):
        # Configure layout weights for responsiveness
        self.grid_rowconfigure(4, weight=1)  # Log/console box expands
        self.grid_columnconfigure(0, weight=1)

        # ----------------------------------------------------
        # 1. HEADER BANNER
        # ----------------------------------------------------
        self.header_frame = ctk.CTkFrame(self, corner_radius=10, fg_color=("gray90", "gray15"))
        self.header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        self.header_frame.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(
            self.header_frame, 
            text="⬇️ YouTube Media Downloader", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(15, 5), sticky="w")

        self.subtitle_label = ctk.CTkLabel(
            self.header_frame, 
            text="Download high-quality videos and audio seamlessly.",
            font=ctk.CTkFont(size=13),
            text_color="gray"
        )
        self.subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="w")

        # ----------------------------------------------------
        # 2. INPUT & ANALYZE FRAME
        # ----------------------------------------------------
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.url_label = ctk.CTkLabel(self.input_frame, text="YouTube URL (Video, Playlist, or Audio):", font=ctk.CTkFont(weight="bold"))
        self.url_label.grid(row=0, column=0, columnspan=2, padx=15, pady=(10, 5), sticky="w")

        self.url_entry = ctk.CTkEntry(
            self.input_frame, 
            textvariable=self.url_var, 
            placeholder_text="https://www.youtube.com/watch?v=..."
        )
        self.url_entry.grid(row=1, column=0, padx=(15, 10), pady=(0, 15), sticky="ew")

        self.analyze_button = ctk.CTkButton(
            self.input_frame, 
            text="Analyze Link", 
            width=120, 
            command=self.start_fetch_info,
            font=ctk.CTkFont(weight="bold")
        )
        self.analyze_button.grid(row=1, column=1, padx=(0, 15), pady=(0, 15), sticky="e")

        # ----------------------------------------------------
        # 3. VIDEO METADATA CARD (Hidden/Blank Initially)
        # ----------------------------------------------------
        self.meta_frame = ctk.CTkFrame(self)
        self.meta_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.meta_frame.grid_columnconfigure(1, weight=1)

        self.meta_title_lbl = ctk.CTkLabel(self.meta_frame, text="Video Information", font=ctk.CTkFont(weight="bold", size=14))
        self.meta_title_lbl.grid(row=0, column=0, columnspan=2, padx=15, pady=(10, 5), sticky="w")

        self.video_title_lbl = ctk.CTkLabel(self.meta_frame, text="Title:", font=ctk.CTkFont(weight="bold"))
        self.video_title_lbl.grid(row=1, column=0, padx=(15, 5), pady=2, sticky="w")
        self.video_title_val = ctk.CTkLabel(self.meta_frame, text="None (Enter a URL and click Analyze)", text_color="gray")
        self.video_title_val.grid(row=1, column=1, padx=(5, 15), pady=2, sticky="w")

        self.channel_lbl = ctk.CTkLabel(self.meta_frame, text="Channel:", font=ctk.CTkFont(weight="bold"))
        self.channel_lbl.grid(row=2, column=0, padx=(15, 5), pady=2, sticky="w")
        self.channel_val = ctk.CTkLabel(self.meta_frame, text="--", text_color="gray")
        self.channel_val.grid(row=2, column=1, padx=(5, 15), pady=2, sticky="w")

        self.duration_lbl = ctk.CTkLabel(self.meta_frame, text="Duration:", font=ctk.CTkFont(weight="bold"))
        self.duration_lbl.grid(row=3, column=0, padx=(15, 5), pady=(2, 15), sticky="w")
        self.duration_val = ctk.CTkLabel(self.meta_frame, text="--", text_color="gray")
        self.duration_val.grid(row=3, column=1, padx=(5, 15), pady=(2, 15), sticky="w")

        # ----------------------------------------------------
        # 4. DOWNLOAD OPTIONS & SAVE PATH
        # ----------------------------------------------------
        self.settings_frame = ctk.CTkFrame(self)
        self.settings_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        self.settings_frame.grid_columnconfigure(1, weight=1)

        self.settings_title = ctk.CTkLabel(self.settings_frame, text="Download Configuration", font=ctk.CTkFont(weight="bold", size=14))
        self.settings_title.grid(row=0, column=0, columnspan=3, padx=15, pady=(10, 5), sticky="w")

        # Quality dropdown
        self.quality_lbl = ctk.CTkLabel(self.settings_frame, text="Preferred Quality:", font=ctk.CTkFont(weight="bold"))
        self.quality_lbl.grid(row=1, column=0, padx=(15, 10), pady=10, sticky="w")

        self.quality_menu = ctk.CTkOptionMenu(
            self.settings_frame,
            values=["Best Quality", "1080p", "720p", "480p", "360p", "Audio Only (MP3)"],
            variable=self.quality_var
        )
        self.quality_menu.grid(row=1, column=1, columnspan=2, padx=(0, 15), pady=10, sticky="ew")

        # Destination Directory
        self.dir_lbl = ctk.CTkLabel(self.settings_frame, text="Save Destination:", font=ctk.CTkFont(weight="bold"))
        self.dir_lbl.grid(row=2, column=0, padx=(15, 10), pady=(0, 15), sticky="w")

        self.dir_entry = ctk.CTkEntry(self.settings_frame, textvariable=self.path_var)
        self.dir_entry.grid(row=2, column=1, padx=(0, 10), pady=(0, 15), sticky="ew")

        self.browse_btn = ctk.CTkButton(
            self.settings_frame, 
            text="Browse...", 
            width=80, 
            command=self.browse_directory
        )
        self.browse_btn.grid(row=2, column=2, padx=(0, 15), pady=(0, 15), sticky="e")

        # Switches for Playlist and Anti-Detection Delay
        self.switches_frame = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        self.switches_frame.grid(row=3, column=0, columnspan=3, padx=15, pady=(5, 15), sticky="w")

        self.playlist_var = ctk.BooleanVar(value=True)
        self.playlist_switch = ctk.CTkSwitch(
            self.switches_frame,
            text="Download entire playlist / channel",
            variable=self.playlist_var,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.playlist_switch.grid(row=0, column=0, padx=(0, 20), pady=5, sticky="w")

        self.delay_var = ctk.BooleanVar(value=True)
        self.delay_switch = ctk.CTkSwitch(
            self.switches_frame,
            text="Enable anti-detection delay (10s)",
            variable=self.delay_var,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.delay_switch.grid(row=0, column=1, padx=0, pady=5, sticky="w")

        # ----------------------------------------------------
        # 5. DOWNLOAD ACTIONS & LIVE PROGRESS
        # ----------------------------------------------------
        self.action_frame = ctk.CTkFrame(self)
        self.action_frame.grid(row=4, column=0, padx=20, pady=10, sticky="nsew")
        self.action_frame.grid_columnconfigure(0, weight=1)
        self.action_frame.grid_rowconfigure(4, weight=1)  # log textbox expands inside this frame

        # Download Button
        self.download_button = ctk.CTkButton(
            self.action_frame, 
            text="⚡ Start Download", 
            height=40, 
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.start_download
        )
        self.download_button.grid(row=0, column=0, padx=15, pady=15, sticky="ew")

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self.action_frame)
        self.progress_bar.grid(row=1, column=0, padx=15, pady=(5, 2), sticky="ew")
        self.progress_bar.set(0.0)

        # Progress stats grid
        self.progress_stats_frame = ctk.CTkFrame(self.action_frame, fg_color="transparent")
        self.progress_stats_frame.grid(row=2, column=0, padx=15, pady=(0, 10), sticky="ew")
        self.progress_stats_frame.grid_columnconfigure(0, weight=1)

        self.percentage_label = ctk.CTkLabel(self.progress_stats_frame, text="0.0%", font=ctk.CTkFont(weight="bold"))
        self.percentage_label.grid(row=0, column=0, sticky="w")

        self.speed_eta_label = ctk.CTkLabel(self.progress_stats_frame, text="Speed: -- | ETA: --", text_color="gray")
        self.speed_eta_label.grid(row=0, column=1, sticky="e")

        # Log terminal
        self.log_lbl = ctk.CTkLabel(self.action_frame, text="Live Log Terminal:", font=ctk.CTkFont(weight="bold"))
        self.log_lbl.grid(row=3, column=0, padx=15, pady=(5, 0), sticky="w")

        self.log_textbox = ctk.CTkTextbox(self.action_frame, font=ctk.CTkFont(family="Courier", size=12))
        self.log_textbox.grid(row=4, column=0, padx=15, pady=(0, 15), sticky="nsew")
        self.log_textbox.configure(state="disabled")

    # ----------------------------------------------------
    # CORE LOGIC & ACTIONS
    # ----------------------------------------------------
    def log_initial_status(self):
        """Output environment and status info on launch."""
        self.show_log("--- YouTube Downloader System Initialized ---")
        if self.ffmpeg_available:
            self.show_log("✅ FFmpeg: Detected! All premium qualities (1080p, 1440p, 4K) & MP3 encoding are supported.")
        else:
            self.show_log("⚠️ Warning: FFmpeg NOT detected in system PATH.")
            self.show_log("   • Quality limits: Fallback to best pre-merged stream (usually up to 720p).")
            self.show_log("   • Audio Only: Downloaded as raw M4A/WebM rather than MP3.")
            self.show_log("   To unlock HD merging & MP3, please download and install FFmpeg.")
        self.show_log("--------------------------------------------")

    def show_log(self, message):
        """Thread-safe interface to write to console."""
        self.safe_log(message)

    def safe_log(self, message):
        """Schedules UI logs on the main event loop."""
        self.after(0, self._append_log, message)

    def _append_log(self, message):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", f"{message}\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def browse_directory(self):
        """Browse folder dialog."""
        folder = filedialog.askdirectory(initialdir=self.path_var.get())
        if folder:
            self.path_var.set(folder)

    # ----------------------------------------------------
    # INFO FETCHING FLOW (THREADED)
    # ----------------------------------------------------
    def start_fetch_info(self):
        url = self.url_var.get().strip()
        if not url:
            self.show_log("❌ Error: Please paste a YouTube link before analyzing.")
            return

        # Disable buttons and set busy text
        self.analyze_button.configure(state="disabled", text="Analyzing...")
        self.video_title_val.configure(text="Fetching details from YouTube...", text_color="yellow")
        self.channel_val.configure(text="--", text_color="gray")
        self.duration_val.configure(text="--", text_color="gray")

        # Threaded execution
        thread = threading.Thread(target=self._fetch_info_thread, args=(url,), daemon=True)
        thread.start()

    def _fetch_info_thread(self, url):
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'noplaylist': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                title = info.get('title', 'Unknown Title')
                uploader = info.get('uploader', 'Unknown Channel')
                duration_sec = info.get('duration')
                
                # Format duration
                if duration_sec:
                    hours = duration_sec // 3600
                    minutes = (duration_sec % 3600) // 60
                    seconds = duration_sec % 60
                    if hours > 0:
                        duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                    else:
                        duration_str = f"{minutes:02d}:{seconds:02d}"
                else:
                    duration_str = "Unknown"

                self.after(0, self._on_fetch_success, title, uploader, duration_str)
        except Exception as e:
            self.after(0, self._on_fetch_error, str(e))

    def _on_fetch_success(self, title, uploader, duration_str):
        self.video_title_val.configure(text=title, text_color=("black", "white"))
        self.channel_val.configure(text=uploader, text_color=("black", "white"))
        self.duration_val.configure(text=duration_str, text_color=("black", "white"))
        
        self.analyze_button.configure(state="normal", text="Analyze Link")
        self.show_log(f"✅ Successfully fetched info: \"{title}\"")

    def _on_fetch_error(self, error_message):
        self.video_title_val.configure(text="Failed to fetch video details.", text_color="red")
        self.channel_val.configure(text="--", text_color="gray")
        self.duration_val.configure(text="--", text_color="gray")
        
        self.analyze_button.configure(state="normal", text="Analyze Link")
        self.show_log(f"❌ Analysis Error: {error_message}")

    # ----------------------------------------------------
    # DOWNLOADING FLOW (THREADED)
    # ----------------------------------------------------
    def start_download(self):
        url = self.url_var.get().strip()
        if not url:
            self.show_log("❌ Error: Please enter a YouTube link.")
            return

        save_path = self.path_var.get().strip()
        if not os.path.exists(save_path):
            self.show_log(f"❌ Error: The destination path '{save_path}' does not exist.")
            return

        quality = self.quality_var.get()

        # Update UI state
        self.download_button.configure(state="disabled", text="⏳ Downloading...")
        self.analyze_button.configure(state="disabled")
        self.progress_bar.set(0.0)
        self.percentage_label.configure(text="0.0%")
        self.speed_eta_label.configure(text="Connecting to download streams...")

        self.show_log(f"🚀 Initializing download...")
        self.show_log(f"   • Destination: {save_path}")
        self.show_log(f"   • Quality Target: {quality}")

        # Start thread
        thread = threading.Thread(target=self._download_thread, args=(url, quality, save_path), daemon=True)
        thread.start()

    @staticmethod
    def get_ydl_opts(url, quality, save_path, ffmpeg_available, logger=None, progress_hook=None):
        ydl_opts = {
            'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
            'noplaylist': "/playlist?" not in url,
        }
        if logger:
            ydl_opts['logger'] = logger
        if progress_hook:
            ydl_opts['progress_hooks'] = [progress_hook]

        if quality == "Audio Only (MP3)":
            ydl_opts['format'] = 'bestaudio/best'
            if ffmpeg_available:
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
        else:
            if ffmpeg_available:
                if quality == "Best Quality":
                    ydl_opts['format'] = 'bestvideo+bestaudio/best'
                elif quality == "1080p":
                    ydl_opts['format'] = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]'
                elif quality == "720p":
                    ydl_opts['format'] = 'bestvideo[height<=720]+bestaudio/best[height<=720]'
                elif quality == "480p":
                    ydl_opts['format'] = 'bestvideo[height<=480]+bestaudio/best[height<=480]'
                elif quality == "360p":
                    ydl_opts['format'] = 'bestvideo[height<=360]+bestaudio/best[height<=360]'
                ydl_opts['merge_output_format'] = 'mp4'
            else:
                if quality in ["Best Quality", "1080p", "720p"]:
                    ydl_opts['format'] = 'best'
                elif quality == "480p":
                    ydl_opts['format'] = 'best[height<=480]'
                elif quality == "360p":
                    ydl_opts['format'] = 'best[height<=360]'
        return ydl_opts

    def _download_thread(self, url, quality, save_path):
        try:
            # Build smart yt-dlp configuration using the testable get_ydl_opts helper
            ydl_opts = self.get_ydl_opts(
                url=url,
                quality=quality,
                save_path=save_path,
                ffmpeg_available=self.ffmpeg_available,
                logger=YDLLogger(self),
                progress_hook=self._ydl_progress_hook
            )

            # Log informative details about chosen strategy
            if quality == "Audio Only (MP3)":
                if self.ffmpeg_available:
                    self.show_log("🎙️ Requesting MP3 conversion (FFmpeg active)...")
                else:
                    self.show_log("🎙️ Downloading native audio format (No FFmpeg to convert to MP3)...")
            else:
                if self.ffmpeg_available:
                    self.show_log("🎥 Merging high-quality streams into MP4 wrapper...")
                else:
                    self.show_log("⚠️ Fallback active: Merging is disabled because FFmpeg was not detected.")
                    if quality in ["Best Quality", "1080p", "720p"]:
                        self.show_log("🎥 Downloading best pre-merged stream (usually 720p max)...")

            # Execute download
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            self.after(0, self._on_download_success)

        except Exception as e:
            self.after(0, self._on_download_error, str(e))

    # ----------------------------------------------------
    # PROGRESS CALBACKS & STATUS WRAPPING
    # ----------------------------------------------------
    def _ydl_progress_hook(self, d):
        status = d.get('status')
        if status == 'downloading':
            # Extract downloaded and total bytes
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0

            # Calculate ratio
            if total > 0:
                percentage = downloaded / total
            else:
                # Try parsing _percent_str fallback
                percent_str = d.get('_percent_str', '').strip()
                if percent_str:
                    try:
                        clean_percent = ''.join(c for c in percent_str if c.isdigit() or c == '.')
                        percentage = float(clean_percent) / 100.0
                    except ValueError:
                        percentage = 0.0
                else:
                    percentage = 0.0

            speed_str = d.get('_speed_str', '0 B/s').strip()
            eta_str = d.get('_eta_str', 'Unknown').strip()

            # Pass coordinates to the main UI thread safely
            self.after(0, self._on_download_progress, percentage, speed_str, eta_str)

        elif status == 'finished':
            # Completed downloading a stream (can happen multiple times during audio+video processes)
            self.after(0, self._on_download_part_finished, d.get('filename', 'file'))

    def _on_download_progress(self, percentage, speed_str, eta_str):
        self.progress_bar.set(percentage)
        self.percentage_label.configure(text=f"{percentage * 100:.1f}%")
        self.speed_eta_label.configure(text=f"Speed: {speed_str} | ETA: {eta_str}")

    def _on_download_part_finished(self, filename):
        name = os.path.basename(filename)
        self.show_log(f"📦 Completed downloading part: {name}")

    def _on_download_success(self):
        self.progress_bar.set(1.0)
        self.percentage_label.configure(text="100.0%")
        self.speed_eta_label.configure(text="Finished!")
        
        self.download_button.configure(state="normal", text="⚡ Start Download")
        self.analyze_button.configure(state="normal")
        
        self.show_log("🎉 Success! Media download & post-processing completed successfully!")
        self.show_log("--------------------------------------------")

    def _on_download_error(self, error_message):
        self.progress_bar.set(0.0)
        self.percentage_label.configure(text="0.0%")
        self.speed_eta_label.configure(text="Download failed.")
        
        self.download_button.configure(state="normal", text="⚡ Start Download")
        self.analyze_button.configure(state="normal")
        
        self.show_log(f"❌ Download Error: {error_message}")
        self.show_log("--------------------------------------------")


if __name__ == "__main__":
    app = YouTubeDownloaderApp()
    app.mainloop()
