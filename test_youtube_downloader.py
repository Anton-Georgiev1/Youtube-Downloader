import os
import unittest
from youtube_downloader import YouTubeDownloaderApp


class TestYouTubeDownloader(unittest.TestCase):
    def test_get_ydl_opts_ffmpeg_available_video(self):
        """Test video option configurations when FFmpeg is available."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        save_path = "/downloads"
        
        # Test Best Quality
        opts = YouTubeDownloaderApp.get_ydl_opts(
            url=url,
            quality="Best Quality",
            save_path=save_path,
            ffmpeg_available=True
        )
        self.assertEqual(opts['format'], 'bestvideo+bestaudio/best')
        self.assertEqual(opts['merge_output_format'], 'mp4')
        self.assertTrue(opts['noplaylist'])
        self.assertEqual(opts['outtmpl'], os.path.join(save_path, '%(title)s.%(ext)s'))

        # Test 1080p
        opts = YouTubeDownloaderApp.get_ydl_opts(
            url=url,
            quality="1080p",
            save_path=save_path,
            ffmpeg_available=True
        )
        self.assertEqual(opts['format'], 'bestvideo[height<=1080]+bestaudio/best[height<=1080]')

        # Test 720p
        opts = YouTubeDownloaderApp.get_ydl_opts(
            url=url,
            quality="720p",
            save_path=save_path,
            ffmpeg_available=True
        )
        self.assertEqual(opts['format'], 'bestvideo[height<=720]+bestaudio/best[height<=720]')

        # Test 360p
        opts = YouTubeDownloaderApp.get_ydl_opts(
            url=url,
            quality="360p",
            save_path=save_path,
            ffmpeg_available=True
        )
        self.assertEqual(opts['format'], 'bestvideo[height<=360]+bestaudio/best[height<=360]')

    def test_get_ydl_opts_ffmpeg_missing_video(self):
        """Test video option configurations fallback when FFmpeg is missing."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        save_path = "/downloads"

        # Test Best Quality fallback
        opts = YouTubeDownloaderApp.get_ydl_opts(
            url=url,
            quality="Best Quality",
            save_path=save_path,
            ffmpeg_available=False
        )
        self.assertEqual(opts['format'], 'best')
        self.assertNotIn('merge_output_format', opts)

        # Test 1080p / 720p fallback
        opts = YouTubeDownloaderApp.get_ydl_opts(
            url=url,
            quality="720p",
            save_path=save_path,
            ffmpeg_available=False
        )
        self.assertEqual(opts['format'], 'best')

        # Test 480p fallback
        opts = YouTubeDownloaderApp.get_ydl_opts(
            url=url,
            quality="480p",
            save_path=save_path,
            ffmpeg_available=False
        )
        self.assertEqual(opts['format'], 'best[height<=480]')

    def test_get_ydl_opts_audio(self):
        """Test audio option configurations with and without FFmpeg."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        save_path = "/downloads"

        # Audio with FFmpeg (MP3 extraction postprocessor active)
        opts = YouTubeDownloaderApp.get_ydl_opts(
            url=url,
            quality="Audio Only (MP3)",
            save_path=save_path,
            ffmpeg_available=True
        )
        self.assertEqual(opts['format'], 'bestaudio/best')
        self.assertIn('postprocessors', opts)
        self.assertEqual(opts['postprocessors'][0]['key'], 'FFmpegExtractAudio')
        self.assertEqual(opts['postprocessors'][0]['preferredcodec'], 'mp3')

        # Audio without FFmpeg (Native download, no postprocessors)
        opts = YouTubeDownloaderApp.get_ydl_opts(
            url=url,
            quality="Audio Only (MP3)",
            save_path=save_path,
            ffmpeg_available=False
        )
        self.assertEqual(opts['format'], 'bestaudio/best')
        self.assertNotIn('postprocessors', opts)

    def test_get_ydl_opts_playlists(self):
        """Test that playlists are handled correctly based on URL structure."""
        save_path = "/downloads"
        
        # Standard video link (with playlist parameters ignored)
        video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PL4o29bINVT4EG_y-k5jGoOu3-Am8Nvi10"
        opts = YouTubeDownloaderApp.get_ydl_opts(
            url=video_url,
            quality="Best Quality",
            save_path=save_path,
            ffmpeg_available=True
        )
        self.assertTrue(opts['noplaylist'])

        # Explicit playlist link
        playlist_url = "https://www.youtube.com/playlist?list=PL4o29bINVT4EG_y-k5jGoOu3-Am8Nvi10"
        opts = YouTubeDownloaderApp.get_ydl_opts(
            url=playlist_url,
            quality="Best Quality",
            save_path=save_path,
            ffmpeg_available=True
        )
        self.assertFalse(opts['noplaylist'])


if __name__ == "__main__":
    unittest.main()
