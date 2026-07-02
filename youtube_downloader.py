import os
import sys
import shutil
import threading
import platform
import json
from pathlib import Path
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import yt_dlp

# Set color theme globally
ctk.set_default_color_theme("blue")

CONFIG_FILE = "ytdl_config.json"


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

        # Threading Events for Pause and Stop mechanics
        self.pause_event = threading.Event()
        self.pause_event.set()  # Set to True (Running state) by default
        self.stop_event = threading.Event()

        # Load saved configurations
        config = self.load_config()

        # Main variables (Initialized with saved values or defaults)
        self.url_var = ctk.StringVar()
        self.quality_var = ctk.StringVar(value=config.get("quality", "Highly Compatible (MP4 - 1080p Max)"))
        self.path_var = ctk.StringVar(value=config.get("download_path"))
        self.autoclear_var = ctk.BooleanVar(value=config.get("autoclear", False))
        self.playlist_var = ctk.BooleanVar(value=config.get("playlist", True))
        self.theme_var = ctk.StringVar(value=config.get("theme", "Light"))
        
        # Settings Variables
        self.show_log_var = ctk.BooleanVar(value=config.get("show_log", False))
        self.show_popup_var = ctk.BooleanVar(value=config.get("show_popup", True))

        # Apply appearance configuration before building components
        ctk.set_appearance_mode(self.theme_var.get())

        # Window configuration
        self.title("⬇️ YouTube Downloader")
        self.geometry("750x830")
        self.minsize(650, 830)

        # Locate FFmpeg
        self.ffmpeg_path = self.get_ffmpeg_path()
        self.ffmpeg_available = self.ffmpeg_path is not None

        # Build GUI
        self.setup_ui()

        # Apply visibility settings based on loaded configurations
        self.update_log_visibility()

        # Log initial environment info
        self.log_initial_status()

    # ----------------------------------------------------
    # CONFIGURATION HANDLING
    # ----------------------------------------------------
    def load_config(self):
        """Load all saved settings from the configuration file."""
        default_path = str(Path.home() / "Downloads")
        if not os.path.exists(default_path):
            default_path = os.getcwd()
            
        defaults = {
            "download_path": default_path,
            "quality": "Highly Compatible (MP4 - 1080p Max)",
            "autoclear": False,
            "playlist": True,
            "theme": "Light",
            "show_log": False,
            "show_popup": True
        }

        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    defaults.update(data)  # Overwrite defaults with saved data
        except Exception:
            pass
        return defaults

    def save_config(self, *args):
        """Save the current state of all settings."""
        try:
            data = {
                "download_path": self.path_var.get(),
                "quality": self.quality_var.get(),
                "autoclear": self.autoclear_var.get(),
                "playlist": self.playlist_var.get(),
                "theme": self.theme_var.get(),
                "show_log": self.show_log_var.get(),
                "show_popup": self.show_popup_var.get()
            }
            with open(CONFIG_FILE, "w") as f:
                json.dump(data, f)
        except Exception:
            pass

    def get_ffmpeg_path(self):
        """Intelligently locate FFmpeg, even if it's placed right next to the script."""
        exe_name = "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg"
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        local_path = os.path.join(script_dir, exe_name)
        if os.path.exists(local_path):
            return local_path
            
        cwd_path = os.path.join(os.getcwd(), exe_name)
        if os.path.exists(cwd_path):
            return cwd_path
            
        sys_path = shutil.which("ffmpeg")
        if sys_path:
            return sys_path
            
        return None

    def toggle_theme(self):
        """Toggle between Light and Dark mode."""
        if self.theme_var.get() == "Light":
            self.theme_var.set("Dark")
            ctk.set_appearance_mode("Dark")
            self.theme_btn.configure(text="🌙 Dark")
        else:
            self.theme_var.set("Light")
            ctk.set_appearance_mode("Light")
            self.theme_btn.configure(text="🌞 Light")
        self.save_config()
        self.show_log(f"🎨 Theme changed to: {self.theme_var.get()}")

    def update_log_visibility(self):
        """Dynamically toggles terminal logs and scales application height."""
        if self.show_log_var.get():
            self.log_lbl.grid(row=3, column=0, padx=15, pady=(5, 0), sticky="w")
            self.log_textbox.grid(row=4, column=0, padx=15, pady=(0, 15), sticky="nsew")
            self.minsize(650, 1000)
            self.geometry("750x1000")
        else:
            self.log_lbl.grid_forget()
            self.log_textbox.grid_forget()
            self.minsize(650, 900)
            self.geometry("750x900")

    def toggle_log_switch(self):
        """Triggers UI layout reorganization and updates saved config state."""
        self.update_log_visibility()
        self.save_config()

    def reset_defaults(self):
        """Restore all variables and settings back to original defaults."""
        default_path = str(Path.home() / "Downloads")
        if not os.path.exists(default_path):
            default_path = os.getcwd()

        self.path_var.set(default_path)
        self.quality_var.set("Highly Compatible (MP4 - 1080p Max)")
        self.autoclear_var.set(False)
        self.playlist_var.set(True)
        self.theme_var.set("Light")
        self.show_log_var.set(False)
        self.show_popup_var.set(True)

        # Apply reset UI styles
        ctk.set_appearance_mode("Light")
        self.theme_btn.configure(text="🌞 Light")
        self.update_log_visibility()
        self.save_config()
        self.show_log("🔄 Configuration reset to default settings.")

    def setup_ui(self):
        self.grid_rowconfigure(4, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ----------------------------------------------------
        # 1. HEADER BANNER
        # ----------------------------------------------------
        self.header_frame = ctk.CTkFrame(self, corner_radius=10, fg_color=("gray90", "gray15"))
        self.header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        self.header_frame.grid_columnconfigure(0, weight=1)
        self.header_frame.grid_columnconfigure(1, weight=0)

        self.title_label = ctk.CTkLabel(
            self.header_frame, 
            text="⬇️ YouTube Downloader", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(15, 5), sticky="w")

        # Theme Toggle Button next to the Title
        current_theme = self.theme_var.get()
        btn_text = "🌞 Light" if current_theme == "Light" else "🌙 Dark"
        self.theme_btn = ctk.CTkButton(
            self.header_frame,
            text=btn_text,
            width=95,
            height=32,
            command=self.toggle_theme,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("gray80", "gray25"),
            hover_color=("gray70", "gray35"),
            text_color=("black", "white")  # Standard legibility text colors
        )
        self.theme_btn.grid(row=0, column=1, padx=20, pady=(15, 5), sticky="e")

        self.subtitle_label = ctk.CTkLabel(
            self.header_frame, 
            text="Download high-quality videos and audio seamlessly.",
            font=ctk.CTkFont(size=13),
            text_color="gray"
        )
        self.subtitle_label.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 15), sticky="w")

        # ----------------------------------------------------
        # 2. INPUT & ANALYZE FRAME
        # ----------------------------------------------------
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.url_label = ctk.CTkLabel(self.input_frame, text="YouTube URL (Video, Playlist, or Audio):", font=ctk.CTkFont(weight="bold"))
        self.url_label.grid(row=0, column=0, columnspan=2, padx=15, pady=(10, 5), sticky="w")

        # Link Toolbar Frame (Entry + Copy/Paste/Clear)
        self.url_toolbar_frame = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        self.url_toolbar_frame.grid(row=1, column=0, columnspan=2, padx=15, pady=(0, 10), sticky="ew")
        self.url_toolbar_frame.grid_columnconfigure(0, weight=1)

        self.url_entry = ctk.CTkEntry(
            self.url_toolbar_frame, 
            textvariable=self.url_var, 
            placeholder_text="..."
        )
        self.url_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        self.paste_btn = ctk.CTkButton(self.url_toolbar_frame, text="📋 Paste", width=60, command=self.paste_link)
        self.paste_btn.grid(row=0, column=1, padx=(0, 5))

        self.copy_btn = ctk.CTkButton(self.url_toolbar_frame, text="📄 Copy", width=60, command=self.copy_link)
        self.copy_btn.grid(row=0, column=2, padx=(0, 5))

        self.clear_btn = ctk.CTkButton(self.url_toolbar_frame, text="❌ Clear", width=60, command=self.clear_link)
        self.clear_btn.grid(row=0, column=3, padx=(0, 0))

        # Auto Clear Switch
        self.autoclear_switch = ctk.CTkSwitch(
            self.input_frame,
            text="Auto-clear URL after successful download",
            variable=self.autoclear_var,
            command=self.save_config,  # Saves state automatically when clicked
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.autoclear_switch.grid(row=2, column=0, columnspan=2, padx=15, pady=(0, 10), sticky="w")

        # Analyze Button
        self.analyze_button = ctk.CTkButton(
            self.input_frame, 
            text="Analyze Link", 
            width=120, 
            command=self.start_fetch_info,
            font=ctk.CTkFont(weight="bold")
        )
        self.analyze_button.grid(row=3, column=0, columnspan=2, padx=15, pady=(0, 15), sticky="e")

        # ----------------------------------------------------
        # 3. VIDEO METADATA CARD
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
        self.settings_title.grid(row=0, column=0, padx=15, pady=(10, 5), sticky="w")

        ffmpeg_status = "✅ FFmpeg: Active (MP4/MP3 Enabled)" if self.ffmpeg_available else "❌ FFmpeg: Missing (MP3/MP4 Merging Disabled)"
        ffmpeg_color = "green" if self.ffmpeg_available else "red"
        
        self.ffmpeg_status_lbl = ctk.CTkLabel(self.settings_frame, text=ffmpeg_status, text_color=ffmpeg_color, font=ctk.CTkFont(weight="bold", size=12))
        self.ffmpeg_status_lbl.grid(row=0, column=1, columnspan=2, padx=15, pady=(10, 5), sticky="e")

        # Quality dropdown
        self.quality_lbl = ctk.CTkLabel(self.settings_frame, text="Preferred Quality:", font=ctk.CTkFont(weight="bold"))
        self.quality_lbl.grid(row=1, column=0, padx=(15, 10), pady=10, sticky="w")

        self.quality_menu = ctk.CTkOptionMenu(
            self.settings_frame,
            values=["Highly Compatible (MP4 - 1080p Max)", "Audio Only (MP3)"],
            variable=self.quality_var,
            command=self.save_config  # Saves state automatically when clicked
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

        # Switches & Configuration Controls Panel
        self.switches_frame = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        self.switches_frame.grid(row=3, column=0, columnspan=3, padx=15, pady=(5, 15), sticky="ew")
        self.switches_frame.grid_columnconfigure(0, weight=1)
        self.switches_frame.grid_columnconfigure(1, weight=0)

        self.playlist_switch = ctk.CTkSwitch(
            self.switches_frame,
            text="Download entire playlist (Enables 10s delay to prevent ban)",
            variable=self.playlist_var,
            command=self.save_config,  # Saves state automatically when clicked
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.playlist_switch.grid(row=0, column=0, columnspan=2, padx=(0, 20), pady=4, sticky="w")

        self.show_log_switch = ctk.CTkSwitch(
            self.switches_frame,
            text="Show Live Log Terminal",
            variable=self.show_log_var,
            command=self.toggle_log_switch,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.show_log_switch.grid(row=1, column=0, columnspan=2, padx=(0, 20), pady=4, sticky="w")

        self.show_popup_switch = ctk.CTkSwitch(
            self.switches_frame,
            text="Show Popup notification on completion",
            variable=self.show_popup_var,
            command=self.save_config,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.show_popup_switch.grid(row=2, column=0, padx=(0, 20), pady=4, sticky="w")

        self.reset_btn = ctk.CTkButton(
            self.switches_frame,
            text="🔄 Reset Defaults",
            width=130,
            fg_color=("gray75", "gray30"),
            hover_color=("gray65", "gray40"),
            text_color=("black", "white"),
            command=self.reset_defaults,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.reset_btn.grid(row=2, column=1, padx=(10, 0), pady=4, sticky="e")

        # ----------------------------------------------------
        # 5. DOWNLOAD ACTIONS & LIVE PROGRESS
        # ----------------------------------------------------
        self.action_frame = ctk.CTkFrame(self)
        self.action_frame.grid(row=4, column=0, padx=20, pady=10, sticky="nsew")
        self.action_frame.grid_columnconfigure(0, weight=1)
        self.action_frame.grid_rowconfigure(4, weight=1)

        self.controls_frame = ctk.CTkFrame(self.action_frame, fg_color="transparent")
        self.controls_frame.grid(row=0, column=0, padx=15, pady=15, sticky="ew")
        self.controls_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.download_button = ctk.CTkButton(
            self.controls_frame, 
            text="⚡ Start Download", 
            height=40, 
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.start_download
        )
        self.download_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.pause_button = ctk.CTkButton(
            self.controls_frame, 
            text="⏸️ Pause", 
            height=40, 
            font=ctk.CTkFont(size=14, weight="bold"),
            state="disabled",
            command=self.toggle_pause
        )
        self.pause_button.grid(row=0, column=1, padx=(5, 5), sticky="ew")

        self.stop_button = ctk.CTkButton(
            self.controls_frame, 
            text="⏹️ Stop", 
            height=40, 
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#c93434",
            hover_color="#9e2a2a",
            state="disabled",
            command=self.stop_download
        )
        self.stop_button.grid(row=0, column=2, padx=(5, 0), sticky="ew")

        self.progress_bar = ctk.CTkProgressBar(self.action_frame)
        self.progress_bar.grid(row=1, column=0, padx=15, pady=(5, 2), sticky="ew")
        self.progress_bar.set(0.0)

        self.progress_stats_frame = ctk.CTkFrame(self.action_frame, fg_color="transparent")
        self.progress_stats_frame.grid(row=2, column=0, padx=15, pady=(0, 10), sticky="ew")
        self.progress_stats_frame.grid_columnconfigure(0, weight=1)

        self.percentage_label = ctk.CTkLabel(self.progress_stats_frame, text="0.0%", font=ctk.CTkFont(weight="bold"))
        self.percentage_label.grid(row=0, column=0, sticky="w")

        self.speed_eta_label = ctk.CTkLabel(self.progress_stats_frame, text="Speed: -- | ETA: --", text_color="gray")
        self.speed_eta_label.grid(row=0, column=1, sticky="e")

        self.log_lbl = ctk.CTkLabel(self.action_frame, text="Live Log Terminal:", font=ctk.CTkFont(weight="bold"))
        self.log_textbox = ctk.CTkTextbox(self.action_frame, font=ctk.CTkFont(family="Courier", size=12))
        self.log_textbox.configure(state="disabled")

    # ----------------------------------------------------
    # LINK TOOLBAR ACTIONS
    # ----------------------------------------------------
    def paste_link(self):
        try:
            clipboard_data = self.clipboard_get()
            self.url_var.set(clipboard_data)
        except Exception:
            self.show_log("❌ Error: Clipboard is empty or contains non-text data.")

    def copy_link(self):
        url = self.url_var.get()
        if url:
            self.clipboard_clear()
            self.clipboard_append(url)
            self.show_log("📄 Link copied to clipboard!")

    def clear_link(self):
        self.url_var.set("")

    # ----------------------------------------------------
    # CORE LOGIC & ACTIONS
    # ----------------------------------------------------
    def log_initial_status(self):
        self.show_log("--- YouTube Downloader System Initialized ---")
        if self.ffmpeg_available:
            self.show_log(f"✅ FFmpeg detected at: {self.ffmpeg_path}")
            self.show_log("✅ Full support for MP3 and MP4 merging enabled.")
        else:
            self.show_log("❌ WARNING: FFmpeg was not detected on your system!")
            self.show_log("   • To unlock high-resolution MP4 & MP3 formats, please install FFmpeg.")
            self.show_log("   • Put 'ffmpeg.exe' in the same folder as this script to fix it.")
        self.show_log("--------------------------------------------")

    def show_log(self, message):
        self.safe_log(message)

    def safe_log(self, message):
        self.after(0, self._append_log, message)

    def _append_log(self, message):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", f"{message}\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def browse_directory(self):
        folder = filedialog.askdirectory(initialdir=self.path_var.get())
        if folder:
            self.path_var.set(folder)
            self.save_config()  # Save folder change immediately

    # ----------------------------------------------------
    # BUTTON CONTROLS
    # ----------------------------------------------------
    def toggle_pause(self):
        if self.pause_event.is_set():
            self.pause_event.clear()
            self.pause_button.configure(text="▶️ Resume")
            self.show_log("⏸️ Command received: Download paused.")
            self.speed_eta_label.configure(text="Download Paused")
        else:
            self.pause_event.set()
            self.pause_button.configure(text="⏸️ Pause")
            self.show_log("▶️ Command received: Download resumed.")

    def stop_download(self):
        self.show_log("🛑 Command received: Aborting download...")
        self.stop_event.set()
        if not self.pause_event.is_set():
            self.pause_event.set()
        self.stop_button.configure(state="disabled")
        self.pause_button.configure(state="disabled")

    # ----------------------------------------------------
    # INFO FETCHING FLOW
    # ----------------------------------------------------
    def start_fetch_info(self):
        url = self.url_var.get().strip()
        if not url:
            self.show_log("❌ Error: Please paste a YouTube link before analyzing.")
            return

        self.analyze_button.configure(state="disabled", text="Analyzing...")
        self.video_title_val.configure(text="Fetching details from YouTube...", text_color="yellow")
        self.channel_val.configure(text="--", text_color="gray")
        self.duration_val.configure(text="--", text_color="gray")

        thread = threading.Thread(target=self._fetch_info_thread, args=(url,), daemon=True)
        thread.start()

    def _fetch_info_thread(self, url):
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'noplaylist': not self.playlist_var.get(),
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if 'entries' in info:
                    info = info['entries'][0]

                title = info.get('title', 'Unknown Title')
                uploader = info.get('uploader', 'Unknown Channel')
                duration_sec = info.get('duration')
                
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
    # DOWNLOADING FLOW
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

        # Explicitly save configs in case the user manually typed a new path into the Entry box
        self.save_config()

        quality = self.quality_var.get()

        if not self.ffmpeg_available:
            self.show_log(f"❌ Cannot start download! FFmpeg is missing on your computer.")
            self.show_log("=== HOW TO FIX THIS ===")
            self.show_log("1. Download FFmpeg from: https://github.com/BtbN/FFmpeg-Builds/releases (get 'ffmpeg-master-latest-win64-gpl.zip')")
            self.show_log("2. Open the ZIP file, go into the 'bin' folder.")
            self.show_log("3. Drag 'ffmpeg.exe' into the EXACT SAME FOLDER where this Python script is located.")
            self.show_log("4. Restart this app, and the red missing label should turn green.")
            return

        self.download_button.configure(state="disabled", text="⏳ Downloading...")
        self.analyze_button.configure(state="disabled")
        
        self.pause_button.configure(state="normal", text="⏸️ Pause")
        self.stop_button.configure(state="normal")
        self.stop_event.clear()
        self.pause_event.set()

        self.progress_bar.set(0.0)
        self.percentage_label.configure(text="0.0%")
        self.speed_eta_label.configure(text="Connecting to download streams...")

        self.show_log(f"🚀 Initializing download...")
        self.show_log(f"   • Target Format: {quality}")
        
        if self.playlist_var.get():
            self.show_log("⏳ Playlist switch enabled: A 10-second delay will be added between videos to avoid bans.")

        thread = threading.Thread(target=self._download_thread, args=(url, quality, save_path), daemon=True)
        thread.start()

    def get_ydl_opts(self, url, quality, save_path, ffmpeg_path, extract_playlist=False, logger=None, progress_hook=None):
        ydl_opts = {
            'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
            'noplaylist': not extract_playlist,
        }
        
        if extract_playlist:
            ydl_opts['sleep_interval'] = 10 
        
        if logger:
            ydl_opts['logger'] = logger
        if progress_hook:
            ydl_opts['progress_hooks'] = [progress_hook]

        if ffmpeg_path:
            ydl_opts['ffmpeg_location'] = ffmpeg_path

        # ------------------- QUALITY LOGIC -------------------
        if quality == "Audio Only (MP3)":
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
            
        elif quality == "Highly Compatible (MP4 - 1080p Max)":
            if ffmpeg_path:
                ydl_opts['format'] = 'bestvideo[ext=mp4][vcodec^=avc]+bestaudio[ext=m4a]/best[ext=mp4]/best'
                ydl_opts['merge_output_format'] = 'mp4'
            else:
                ydl_opts['format'] = 'best' 
                
        return ydl_opts

    def _download_thread(self, url, quality, save_path):
        try:
            ydl_opts = self.get_ydl_opts(
                url=url,
                quality=quality,
                save_path=save_path,
                ffmpeg_path=self.ffmpeg_path,
                extract_playlist=self.playlist_var.get(),
                logger=YDLLogger(self),
                progress_hook=self._ydl_progress_hook
            )

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            self.after(0, self._on_download_success)

        except Exception as e:
            self.after(0, self._on_download_error, str(e))

    # ----------------------------------------------------
    # PROGRESS CALBACKS & STATUS WRAPPING
    # ----------------------------------------------------
    def _ydl_progress_hook(self, d):
        if self.stop_event.is_set():
            raise ValueError("Download Cancelled by User")

        if not self.pause_event.is_set():
            self.pause_event.wait()
            if self.stop_event.is_set():
                raise ValueError("Download Cancelled by User")

        status = d.get('status')
        if status == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0

            if total > 0:
                percentage = downloaded / total
            else:
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
            text_eta = d.get('_eta_str', 'Unknown').strip()

            self.after(0, self._on_download_progress, percentage, speed_str, text_eta)

        elif status == 'finished':
            self.after(0, self._on_download_part_finished, d.get('filename', 'file'))

    def _on_download_progress(self, percentage, speed_str, text_eta):
        if self.pause_event.is_set() and not self.stop_event.is_set():
            self.progress_bar.set(percentage)
            self.percentage_label.configure(text=f"{percentage * 100:.1f}%")
            self.speed_eta_label.configure(text=f"Speed: {speed_str} | ETA: {text_eta}")

    def _on_download_part_finished(self, filename):
        name = os.path.basename(filename)
        self.show_log(f"📦 Completed downloading part: {name}")

    def _reset_buttons(self):
        self.download_button.configure(state="normal", text="⚡ Start Download")
        self.analyze_button.configure(state="normal")
        self.pause_button.configure(state="disabled", text="⏸️ Pause")
        self.stop_button.configure(state="disabled")

    def _on_download_success(self):
        self.progress_bar.set(1.0)
        self.percentage_label.configure(text="100.0%")
        self.speed_eta_label.configure(text="Finished!")
        
        self._reset_buttons()
        self.show_log("🎉 Success! Media download & conversion completed correctly!")

        # Completion Popup Message Action (Checks switch configuration state)
        if self.show_popup_var.get():
            messagebox.showinfo("Download Completed", "🎉 Success! Media download & conversion completed correctly!")
        
        # AUTO CLEAN FUNCTIONALITY (Checking the switch)
        if self.autoclear_var.get():
            self.clear_link()
            self.video_title_val.configure(text="None (Enter a URL and click Analyze)", text_color="gray")
            self.channel_val.configure(text="--", text_color="gray")
            self.duration_val.configure(text="--", text_color="gray")
            self.show_log("🧹 URL field auto-cleaned for your next link.")
            
        self.show_log("--------------------------------------------")

    def _on_download_error(self, error_message):
        self.progress_bar.set(0.0)
        self.percentage_label.configure(text="0.0%")
        
        if "Download Cancelled by User" in error_message:
            self.speed_eta_label.configure(text="Cancelled.")
            self.show_log("🛑 The download was successfully cancelled and deleted.")
        else:
            self.speed_eta_label.configure(text="Download failed.")
            self.show_log(f"❌ Download Error: {error_message}")
            
        self._reset_buttons()
        self.show_log("--------------------------------------------")


if __name__ == "__main__":
    app = YouTubeDownloaderApp()
    app.mainloop()