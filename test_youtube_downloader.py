import unittest
from unittest.mock import MagicMock, patch, mock_open
import os
import json
import platform

# Mock Tkinter/Customtkinter components globally before importing the app
# to prevent "no display name" errors on headless CI systems or environments.
class MockStringVar:
    def __init__(self, value=""):
        self.value = value
    def get(self):
        return self.value
    def set(self, val):
        self.value = str(val)

class MockBooleanVar:
    def __init__(self, value=False):
        self.value = value
    def get(self):
        return self.value
    def set(self, val):
        self.value = bool(val)

with patch('customtkinter.CTk.__init__', lambda self, *args, **kwargs: None), \
     patch('customtkinter.StringVar', side_effect=MockStringVar), \
     patch('customtkinter.BooleanVar', side_effect=MockBooleanVar), \
     patch('customtkinter.CTk.title'), \
     patch('customtkinter.CTk.geometry'), \
     patch('customtkinter.CTk.minsize'), \
     patch('youtube_downloader.YouTubeDownloaderApp.setup_ui'):
    
    import youtube_downloader


class TestYouTubeDownloader(unittest.TestCase):

    def setUp(self):
        # Set up a clean instance of the application with patched GUI dependencies
        self.ctk_init_patcher = patch('customtkinter.CTk.__init__', return_value=None)
        self.ctk_init_patcher.start()

        self.title_patcher = patch('customtkinter.CTk.title')
        self.title_patcher.start()
        self.geometry_patcher = patch('customtkinter.CTk.geometry')
        self.geometry_patcher.start()
        self.minsize_patcher = patch('customtkinter.CTk.minsize')
        self.minsize_patcher.start()
        self.grid_row_patcher = patch('customtkinter.CTk.grid_rowconfigure')
        self.grid_row_patcher.start()
        self.grid_col_patcher = patch('customtkinter.CTk.grid_columnconfigure')
        self.grid_col_patcher.start()

        # Mock setup_ui to isolate functional logic from layout generation
        self.setup_ui_patcher = patch('youtube_downloader.YouTubeDownloaderApp.setup_ui')
        self.setup_ui_patcher.start()

        # Mock initial status printing
        self.log_init_patcher = patch('youtube_downloader.YouTubeDownloaderApp.log_initial_status')
        self.log_init_patcher.start()

        # Use mock Tkinter-like variables
        self.string_var_patcher = patch('customtkinter.StringVar', side_effect=MockStringVar)
        self.string_var_patcher.start()
        self.bool_var_patcher = patch('customtkinter.BooleanVar', side_effect=MockBooleanVar)
        self.bool_var_patcher.start()

        # Mock internal update triggers
        self.after_patcher = patch('customtkinter.CTk.after')
        self.mock_after = self.after_patcher.start()

        # Create application instance
        self.app = youtube_downloader.YouTubeDownloaderApp()

    def tearDown(self):
        patch.stopall()

    # -------------------------------------------------------------------------
    # CONFIGURATION & I/O TESTS
    # -------------------------------------------------------------------------
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='{"download_path": "/fake/downloads", "quality": "Audio Only (MP3)", "autoclear": false, "playlist": false}')
    def test_load_config_file_exists(self, mock_file, mock_exists):
        """Verify configurations are correctly read and loaded from a file when present."""
        mock_exists.return_value = True
        config = self.app.load_config()
        self.assertEqual(config["download_path"], "/fake/downloads")
        self.assertEqual(config["quality"], "Audio Only (MP3)")
        self.assertFalse(config["autoclear"])
        self.assertFalse(config["playlist"])

    @patch('os.path.exists')
    def test_load_config_file_missing_fallback(self, mock_exists):
        """Verify default fallback configuration values are generated when file does not exist."""
        mock_exists.return_value = False
        config = self.app.load_config()
        self.assertEqual(config["quality"], "Highly Compatible (MP4 - 1080p Max)")
        self.assertTrue(config["autoclear"])
        self.assertTrue(config["playlist"])

    @patch('builtins.open', new_callable=mock_open)
    def test_save_config(self, mock_file):
        """Verify configuration states are correctly converted to JSON and written to disk."""
        self.app.path_var.set("/test/save")
        self.app.quality_var.set("Highly Compatible (MP4 - 1080p Max)")
        self.app.autoclear_var.set(True)
        self.app.playlist_var.set(True)

        self.app.save_config()

        mock_file.assert_called_with("ytdl_config.json", "w")
        handle = mock_file()
        written_data = "".join(call_args[0][0] for call_args in handle.write.call_args_list)
        parsed_data = json.loads(written_data)

        self.assertEqual(parsed_data["download_path"], "/test/save")
        self.assertEqual(parsed_data["quality"], "Highly Compatible (MP4 - 1080p Max)")
        self.assertTrue(parsed_data["autoclear"])
        self.assertTrue(parsed_data["playlist"])

    # -------------------------------------------------------------------------
    # FFMPEG DETECTION TESTS
    # -------------------------------------------------------------------------
    @patch('platform.system')
    @patch('os.path.exists')
    @patch('shutil.which')
    def test_get_ffmpeg_path_local_windows(self, mock_which, mock_exists, mock_system):
        """Verify the local directory check works on Windows."""
        mock_system.return_value = "Windows"
        mock_exists.side_effect = lambda path: "ffmpeg.exe" in path
        
        path = self.app.get_ffmpeg_path()
        self.assertTrue(path.endswith("ffmpeg.exe"))

    @patch('platform.system')
    @patch('os.path.exists')
    @patch('shutil.which')
    def test_get_ffmpeg_path_system_fallback(self, mock_which, mock_exists, mock_system):
        """Verify fallback triggers system binary path checks."""
        mock_system.return_value = "Linux"
        mock_exists.return_value = False
        mock_which.return_value = "/usr/bin/ffmpeg"

        path = self.app.get_ffmpeg_path()
        self.assertEqual(path, "/usr/bin/ffmpeg")
        mock_which.assert_called_with("ffmpeg")

    # -------------------------------------------------------------------------
    # URL TOOLBAR & CLIPBOARD TESTS
    # -------------------------------------------------------------------------
    def test_clear_link(self):
        """Verify clear function resets target variable."""
        self.app.url_var.set("https://youtube.com/watch?v=123")
        self.app.clear_link()
        self.assertEqual(self.app.url_var.get(), "")

    @patch('youtube_downloader.YouTubeDownloaderApp.clipboard_get')
    def test_paste_link(self, mock_clipboard_get):
        """Verify copy mechanism successfully updates input elements."""
        mock_clipboard_get.return_value = "https://youtube.com/watch?v=abc"
        self.app.paste_link()
        self.assertEqual(self.app.url_var.get(), "https://youtube.com/watch?v=abc")

    @patch('youtube_downloader.YouTubeDownloaderApp.clipboard_clear')
    @patch('youtube_downloader.YouTubeDownloaderApp.clipboard_append')
    def test_copy_link(self, mock_append, mock_clear):
        """Verify content transmission from input element to system clipboard."""
        self.app.url_var.set("https://youtube.com/watch?v=xyz")
        self.app.copy_link()
        mock_clear.assert_called_once()
        mock_append.assert_called_with("https://youtube.com/watch?v=xyz")

    # -------------------------------------------------------------------------
    # PAUSE & STOP mechanics TESTS
    # -------------------------------------------------------------------------
    def test_toggle_pause(self):
        """Verify thread synchronization states change when pause/resume is triggered."""
        self.assertTrue(self.app.pause_event.is_set())
        
        self.app.pause_button = MagicMock()
        self.app.speed_eta_label = MagicMock()
        self.app.safe_log = MagicMock()

        # Pause
        self.app.toggle_pause()
        self.assertFalse(self.app.pause_event.is_set())
        self.app.pause_button.configure.assert_called_with(text="▶️ Resume")

        # Resume
        self.app.toggle_pause()
        self.assertTrue(self.app.pause_event.is_set())
        self.app.pause_button.configure.assert_called_with(text="⏸️ Pause")

    def test_stop_download(self):
        """Verify the cancellation flags update when stop is clicked."""
        self.app.stop_event.clear()
        self.app.pause_event.clear()

        self.app.stop_button = MagicMock()
        self.app.pause_button = MagicMock()
        self.app.safe_log = MagicMock()

        self.app.stop_download()

        self.assertTrue(self.app.stop_event.is_set())
        self.assertTrue(self.app.pause_event.is_set())  # Must unblock paused threads to stop cleanly
        self.app.stop_button.configure.assert_called_with(state="disabled")
        self.app.pause_button.configure.assert_called_with(state="disabled")

    # -------------------------------------------------------------------------
    # YT-DLP FORMAT SELECTION TESTS
    # -------------------------------------------------------------------------
    def test_get_ydl_opts_audio(self):
        """Verify parameters match best practice format specifications for MP3 extraction."""
        opts = self.app.get_ydl_opts(
            url="https://youtube.com/watch?v=xyz",
            quality="Audio Only (MP3)",
            save_path="/dummy/path",
            ffmpeg_path="/bin/ffmpeg",
            extract_playlist=False
        )
        self.assertEqual(opts['format'], 'bestaudio/best')
        self.assertEqual(opts['ffmpeg_location'], '/bin/ffmpeg')
        self.assertEqual(opts['noplaylist'], True)
        self.assertEqual(len(opts['postprocessors']), 1)
        self.assertEqual(opts['postprocessors'][0]['key'], 'FFmpegExtractAudio')
        self.assertEqual(opts['postprocessors'][0]['preferredcodec'], 'mp3')

    def test_get_ydl_opts_video(self):
        """Verify compatibility arguments apply for optimal standard MP4 video processing."""
        opts = self.app.get_ydl_opts(
            url="https://youtube.com/watch?v=xyz",
            quality="Highly Compatible (MP4 - 1080p Max)",
            save_path="/dummy/path",
            ffmpeg_path="/bin/ffmpeg",
            extract_playlist=True
        )
        self.assertIn('bestvideo[ext=mp4]', opts['format'])
        self.assertEqual(opts['merge_output_format'], 'mp4')
        self.assertEqual(opts['noplaylist'], False)
        self.assertEqual(opts['sleep_interval'], 10)  # Verify delay is requested to protect against bans

    # -------------------------------------------------------------------------
    # BACKGROUND THREAD AND HOOK TESTS
    # -------------------------------------------------------------------------
    @patch('yt_dlp.YoutubeDL')
    def test_fetch_info_thread_success_short_duration(self, mock_ytdl_class):
        """Verify metadata parser successfully maps short duration seconds to minutes and seconds format."""
        mock_instance = MagicMock()
        mock_instance.extract_info.return_value = {
            'title': 'Short Test Video',
            'uploader': 'Test Channel',
            'duration': 125
        }
        mock_ytdl_class.return_value.__enter__.return_value = mock_instance

        self.app._fetch_info_thread("https://youtube.com/watch?v=xyz")

        self.mock_after.assert_called_once()
        args = self.mock_after.call_args[0]
        self.assertEqual(args[1], self.app._on_fetch_success)
        self.assertEqual(args[2], 'Short Test Video')
        self.assertEqual(args[3], 'Test Channel')
        self.assertEqual(args[4], '02:05')

    @patch('yt_dlp.YoutubeDL')
    def test_fetch_info_thread_success_long_duration(self, mock_ytdl_class):
        """Verify metadata parser formats durations over an hour into hours, minutes, and seconds format."""
        mock_instance = MagicMock()
        mock_instance.extract_info.return_value = {
            'title': 'Long Test Video',
            'uploader': 'Test Channel',
            'duration': 3665
        }
        mock_ytdl_class.return_value.__enter__.return_value = mock_instance

        self.app._fetch_info_thread("https://youtube.com/watch?v=xyz")

        self.mock_after.assert_called_once()
        args = self.mock_after.call_args[0]
        self.assertEqual(args[1], self.app._on_fetch_success)
        self.assertEqual(args[2], 'Long Test Video')
        self.assertEqual(args[3], 'Test Channel')
        self.assertEqual(args[4], '01:01:05')

    @patch('yt_dlp.YoutubeDL')
    def test_fetch_info_thread_failure(self, mock_ytdl_class):
        """Verify errors during network metadata extraction gracefully report failure to the main loop."""
        mock_instance = MagicMock()
        mock_instance.extract_info.side_effect = Exception("HTTP 403 Forbidden")
        mock_ytdl_class.return_value.__enter__.return_value = mock_instance

        self.app._fetch_info_thread("https://youtube.com/watch?v=xyz")

        self.mock_after.assert_called_once()
        args = self.mock_after.call_args[0]
        self.assertEqual(args[1], self.app._on_fetch_error)
        self.assertIn("HTTP 403 Forbidden", args[2])

    def test_ydl_progress_hook_downloading(self):
        """Verify mathematical calculation mappings for active downloads coordinate values correctly."""
        self.app.percentage_label = MagicMock()
        self.app.speed_eta_label = MagicMock()
        self.app.progress_bar = MagicMock()

        self.app.pause_event.set()
        self.app.stop_event.clear()

        payload = {
            'status': 'downloading',
            'downloaded_bytes': 750,
            'total_bytes': 1000,
            '_speed_str': '5 MB/s',
            '_eta_str': '00:02'
        }

        self.app._ydl_progress_hook(payload)
        
        self.mock_after.assert_called_once()
        
        # Manually invoke progress update callback normally run by 'after'
        self.app._on_download_progress(0.75, '5 MB/s', '00:02')
        self.app.progress_bar.set.assert_called_with(0.75)
        self.app.percentage_label.configure.assert_called_with(text="75.0%")
        self.app.speed_eta_label.configure.assert_called_with(text="Speed: 5 MB/s | ETA: 00:02")

    def test_ydl_progress_hook_aborted_by_stop(self):
        """Verify triggering the stop event raises a cancellation error inside the hook loop."""
        self.app.stop_event.set()
        
        payload = {'status': 'downloading'}
        with self.assertRaises(ValueError) as context:
            self.app._ydl_progress_hook(payload)
        self.assertEqual(str(context.exception), "Download Cancelled by User")


if __name__ == '__main__':
    unittest.main()