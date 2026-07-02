# test_youtube_downloader.py

import os
import json
import platform
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Import target modules from the downloader project
from languages import LANGUAGES, QUALITY_MAP
from youtube_downloader import YouTubeDownloaderApp, CONFIG_FILE

# Check if a display server is available to execute active GUI layout tests
try:
    import tkinter
    temp_root = tkinter.Tk()
    temp_root.destroy()
    DISPLAY_AVAILABLE = True
except Exception:
    DISPLAY_AVAILABLE = False


class TestLanguagesData(unittest.TestCase):
    """Verifies integrity and consistency of localization configuration dictionaries."""

    def test_language_keys_consistency(self):
        """Ensure every language translation contains the exact same dictionary keys to prevent KeyErrors."""
        english_keys = set(LANGUAGES["English"].keys())
        for lang, translation_dict in LANGUAGES.items():
            lang_keys = set(translation_dict.keys())
            self.assertEqual(
                english_keys, 
                lang_keys, 
                f"Keys in '{lang}' dictionary mismatch with 'English' keys. "
                f"Missing: {english_keys - lang_keys}, Extra: {lang_keys - english_keys}"
            )

    def test_quality_map_consistency(self):
        """Ensure every quality map entry has exactly two elements (highly compatible video and audio-only)."""
        for lang, qualities in QUALITY_MAP.items():
            self.assertEqual(
                len(qualities), 
                2, 
                f"Quality map for '{lang}' must have exactly 2 quality elements (video, audio)."
            )


class TestDownloaderLogic(unittest.TestCase):
    """Tests core logical processing methods that do not strictly require a running GUI loop."""

    def test_get_canonical_quality_mapping(self):
        """Verify dynamic and translated quality strings map correctly to internal keys."""
        # Test English translations
        self.assertEqual(
            YouTubeDownloaderApp.get_canonical_quality(None, "Highly Compatible (MP4 - 1080p Max)"),
            "Highly Compatible (MP4 - 1080p Max)"
        )
        self.assertEqual(
            YouTubeDownloaderApp.get_canonical_quality(None, "Audio Only (MP3)"),
            "Audio Only (MP3)"
        )

        # Test foreign translations (e.g., Bulgarian, Spanish)
        self.assertEqual(
            YouTubeDownloaderApp.get_canonical_quality(None, "Висока съвместимост (MP4 - Макс 1080p)"),
            "Highly Compatible (MP4 - 1080p Max)"
        )
        self.assertEqual(
            YouTubeDownloaderApp.get_canonical_quality(None, "Solo audio (MP3)"),
            "Audio Only (MP3)"
        )

        # Fallback test
        self.assertEqual(
            YouTubeDownloaderApp.get_canonical_quality(None, "Invalid Quality Name Option"),
            "Highly Compatible (MP4 - 1080p Max)"
        )

    def test_get_ydl_opts_audio(self):
        """Verify yt-dlp parameter generation for Audio Only (MP3)."""
        opts = YouTubeDownloaderApp.get_ydl_opts(
            self=None,
            url="https://youtube.com/watch?v=123",
            quality="Audio Only (MP3)",
            save_path="/mock/downloads",
            ffmpeg_path="/usr/bin/ffmpeg",
            extract_playlist=False
        )

        self.assertEqual(opts['format'], 'bestaudio/best')
        self.assertEqual(opts['ffmpeg_location'], '/usr/bin/ffmpeg')
        self.assertEqual(opts['noplaylist'], True)
        self.assertIn('postprocessors', opts)
        self.assertEqual(opts['postprocessors'][0]['key'], 'FFmpegExtractAudio')
        self.assertEqual(opts['postprocessors'][0]['preferredcodec'], 'mp3')

    def test_get_ydl_opts_video_with_ffmpeg(self):
        """Verify yt-dlp parameter generation for Highly Compatible MP4 with FFmpeg available."""
        opts = YouTubeDownloaderApp.get_ydl_opts(
            self=None,
            url="https://youtube.com/watch?v=123",
            quality="Highly Compatible (MP4 - 1080p Max)",
            save_path="/mock/downloads",
            ffmpeg_path="/usr/bin/ffmpeg",
            extract_playlist=True
        )

        self.assertIn('bestvideo[ext=mp4]', opts['format'])
        self.assertEqual(opts['merge_output_format'], 'mp4')
        self.assertEqual(opts['noplaylist'], False)
        self.assertEqual(opts['sleep_interval'], 10)

    def test_get_ydl_opts_video_without_ffmpeg(self):
        """Verify yt-dlp fallback configuration when FFmpeg path is absent."""
        opts = YouTubeDownloaderApp.get_ydl_opts(
            self=None,
            url="https://youtube.com/watch?v=123",
            quality="Highly Compatible (MP4 - 1080p Max)",
            save_path="/mock/downloads",
            ffmpeg_path=None,
            extract_playlist=False
        )

        self.assertEqual(opts['format'], 'best')
        self.assertNotIn('merge_output_format', opts)

    @patch("os.path.exists")
    @patch("shutil.which")
    def test_ffmpeg_detection_logic(self, mock_which, mock_exists):
        """Ensure FFmpeg path resolution scans script dir, cwd, and system PATH sequentially."""
        # Case 1: Detect next to script path
        mock_exists.side_effect = lambda path: "youtube_downloader" in path or "ffmpeg" in path
        path = YouTubeDownloaderApp.get_ffmpeg_path(None)
        self.assertIsNotNone(path)

        # Case 2: Found on System PATH
        mock_exists.side_effect = lambda path: False
        mock_which.return_value = "/usr/bin/ffmpeg"
        path = YouTubeDownloaderApp.get_ffmpeg_path(None)
        self.assertEqual(path, "/usr/bin/ffmpeg")

        # Case 3: Missing completely
        mock_which.return_value = None
        path = YouTubeDownloaderApp.get_ffmpeg_path(None)
        self.assertIsNone(path)

    @patch("builtins.open", new_callable=mock_open, read_data='{"language": "Français", "theme": "Dark"}')
    @patch("os.path.exists", return_value=True)
    def test_load_config_custom_values(self, mock_exists, mock_file):
        """Ensure configuration loader reads file parameters and returns correct custom dictionaries."""
        config = YouTubeDownloaderApp.load_config(None)
        self.assertEqual(config["language"], "Français")
        self.assertEqual(config["theme"], "Dark")
        self.assertEqual(config["playlist"], True)  # Fallback to default

    @patch("os.path.exists", return_value=False)
    def test_load_config_fallback_defaults(self, mock_exists):
        """Verify configuration loads sensible hardcoded values when file does not exist."""
        config = YouTubeDownloaderApp.load_config(None)
        self.assertEqual(config["language"], "English")
        self.assertEqual(config["theme"], "Light")
        self.assertTrue(config["playlist"])


@unittest.skipIf(not DISPLAY_AVAILABLE, "Skipping full GUI tests (display interface not available)")
class TestGUIVisuals(unittest.TestCase):
    """Runs interface-focused checks requiring a live graphical window subsystem."""

    @patch("youtube_downloader.YouTubeDownloaderApp.save_config")
    @patch("youtube_downloader.YouTubeDownloaderApp.load_config")
    def setUp(self, mock_load, mock_save):
        # Enforce predictable default settings during initialization
        mock_load.return_value = {
            "download_path": "/mock/downloads",
            "quality": "Highly Compatible (MP4 - 1080p Max)",
            "autoclear": False,
            "playlist": True,
            "theme": "Light",
            "show_log": False,
            "show_popup": True,
            "language": "English"
        }
        # Prevent unit tests from altering settings on disk
        mock_save.side_effect = lambda *args, **kwargs: None

        self.app = YouTubeDownloaderApp()
        self.app.withdraw()  # Keeps window hidden during automated checks

        # Run queued startup tasks (such as logs) before starting actual checks
        try:
            self.app.update_idletasks()
            self.app.update()
        except Exception:
            pass

    def tearDown(self):
        # Flush any last drawing updates to avoid Tcl execution warnings on exit
        try:
            self.app.update_idletasks()
            self.app.update()
        except Exception:
            pass
        self.app.destroy()

    def test_initial_ui_state(self):
        """Check that variables and elements map to configured default load values."""
        self.assertEqual(self.app.language_var.get(), "English")
        self.assertEqual(self.app.theme_var.get(), "Light")
        self.assertEqual(self.app.title_label.cget("text"), "⬇️ YouTube Downloader")

    def test_ui_localization_switch(self):
        """Verify language updates change visual texts to target dictionary mappings."""
        self.app.language_var.set("Español")
        self.app.update_ui_language()

        self.assertEqual(self.app.title_label.cget("text"), "⬇️ Descargador de YouTube")
        self.assertEqual(self.app.subtitle_label.cget("text"), "Descarga videos y audio de alta calidad sin problemas.")
        self.assertEqual(self.app.reset_btn.cget("text"), "🔄 Restablecer ajustes")

    def test_ui_theme_toggle(self):
        """Verify toggling light/dark theme updates variables, appearance mode, and button labels."""
        self.assertEqual(self.app.theme_var.get(), "Light")
        self.app.toggle_theme()

        self.assertEqual(self.app.theme_var.get(), "Dark")
        self.assertEqual(self.app.theme_btn.cget("text"), "🌙 Dark")


if __name__ == "__main__":
    unittest.main()